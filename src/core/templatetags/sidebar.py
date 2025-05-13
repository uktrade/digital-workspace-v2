from typing import Type

from django import template
from django.contrib.contenttypes.models import ContentType
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.safestring import SafeString
from wagtail.models import Page

from core import flags
from core.models.models import SiteAlertBanner
from core.utils import flag_is_active, get_all_feature_flags
from events.models import EventsHome
from home.models import HomePage, QuickLink
from interactions.services import bookmarks as bookmarks_service
from networks.models import Network, NetworksHome
from news.models import NewsPage


register = template.Library()


class SidebarPart:
    template_name: str
    context: dict
    request: dict

    def __init__(self, context: dict) -> None:
        self.context = context
        self.request = context["request"]

    def is_visible(self) -> bool:
        """
        Decide if this part should be visible on the current page.
        """
        return True

    def get_part_context(self) -> dict:
        """
        Build the context to pass into the template.
        """
        return {
            "FEATURE_FLAGS": get_all_feature_flags(self.request),
        }

    def render(self) -> SafeString:
        return render_to_string(self.template_name, self.get_part_context())

    __str__ = render
    __html__ = render


class SidebarSection:
    title: str
    parts: list[SidebarPart] = []
    context: dict
    template_name: str = "tags/sidebar/sections/base.html"

    def __init__(
        self,
        title: str,
        parts: list[Type[SidebarPart]],
        context: dict,
        template_name: str | None = None,
    ):
        self.title = title
        self.parts = [part(context=context) for part in parts]
        self.context = context

        if template_name:
            self.template_name = template_name

    def is_visible(self) -> bool:
        """
        Decide if this section should be visible on the current page.
        """
        return any(part.is_visible() for part in self.parts)

    def get_section_context(self) -> dict[str, list[SidebarPart]]:
        """
        Build the context to pass into the template.
        """
        return {
            "parts": [part for part in self.parts if part.is_visible()],
        }

    def render(self) -> SafeString:
        return render_to_string(self.template_name, self.get_section_context())

    __str__ = render
    __html__ = render


class SiteAlert(SidebarPart):
    template_name = "tags/sidebar/parts/site_alert.html"

    def __init__(self, context: dict) -> None:
        super().__init__(context)
        self.current_alert = SiteAlertBanner.objects.filter(activated=True).first()

    def is_visible(self, *args, **kwargs) -> bool:
        page = self.context.get("self")
        if isinstance(page, HomePage) and self.current_alert:
            return True
        return False

    def get_part_context(self) -> dict:
        context = super().get_part_context()
        context.update(
            banner_text=self.current_alert.banner_text,
            banner_link=self.current_alert.banner_link,
        )
        return context


class GiveFeedback(SidebarPart):
    template_name = "tags/sidebar/parts/feedback.html"

    title = "Give feedback"
    description = "Did you find what you were looking for?"

    def is_visible(self) -> bool:
        page = self.context.get("self")
        if isinstance(page, HomePage):
            return False
        return True

    def get_part_context(self) -> dict:
        context = super().get_part_context()
        context.update(
            title=self.title,
            description=self.description,
        )
        return context


class YourBookmarks(SidebarPart):
    template_name = "interactions/bookmark_card.html"

    def is_visible(self) -> bool:
        page = self.context.get("self")
        if isinstance(page, HomePage):
            return True
        return False

    def get_part_context(self) -> dict:
        context = super().get_part_context()
        context.update(
            user=self.context.get("user"),
        )
        return context


class Bookmark(SidebarPart):
    template_name = "tags/sidebar/parts/bookmark.html"

    def is_visible(self) -> bool:
        page = self.context.get("self")
        if isinstance(page, (HomePage, EventsHome, NetworksHome)):
            return False

        return isinstance(page, Page)

    def get_part_context(self) -> dict:
        context = super().get_part_context()

        user = self.context.get("user")
        page = self.context.get("self")
        is_bookmarked = bookmarks_service.is_page_bookmarked(user, page)
        post_url = reverse("interactions:bookmark")
        context.update(
            post_url=post_url,
            user=user,
            page=page,
            is_bookmarked=is_bookmarked,
            csrf_token=self.context["csrf_token"],
        )
        return context


class Comment(SidebarPart):
    template_name = "tags/sidebar/parts/comment.html"

    def is_visible(self) -> bool:
        page = self.context.get("self")
        return bool(isinstance(page, NewsPage) and page.allow_comments)

    def get_part_context(self) -> dict:
        context = super().get_part_context()

        page = self.context.get("self")
        allow_comments = page.allow_comments

        context.update(
            page=page,
            allow_comments=allow_comments,
        )
        return context


class Share(SidebarPart):
    template_name = "tags/sidebar/parts/share.html"

    def is_visible(self) -> bool:
        page = self.context.get("self")

        if not isinstance(page, Page):
            return False

        return not isinstance(page, HomePage)

    def get_part_context(self) -> dict:
        context = super().get_part_context()
        page = self.context.get("self")

        context.update(
            page=page,
            page_url=page.get_full_url(self.request),
            request=self.request,
        )
        return context


class QuickLinks(SidebarPart):
    template_name = "tags/sidebar/parts/quick_links.html"

    def is_visible(self) -> bool:
        page = self.context.get("self")
        if isinstance(page, HomePage):
            return True
        return False

    def get_part_context(self) -> dict:
        context = super().get_part_context()
        quick_links = [
            {
                "url": obj.link_to.get_url(self.request),
                "text": obj.title,
            }
            for obj in QuickLink.objects.all().order_by("result_weighting", "title")
        ]
        context.update(
            quick_links=quick_links,
        )
        return context


class UsefulLinks(SidebarPart):
    template_name = "tags/sidebar/parts/useful_links.html"
    title = "Useful links"

    def __init__(self, context: dict) -> None:
        super().__init__(context)
        self.page = self.context.get("self")
        self.useful_links = getattr(self.page, "useful_links", [])
        self.child_pages = []
        if isinstance(self.page, (Network, NetworksHome)):
            self.child_pages = (
                self.page.get_children()
                .live()
                .public()
                .exclude(
                    content_type__in=[
                        ContentType.objects.get_for_model(model=NetworksHome),
                        ContentType.objects.get_for_model(model=Network),
                    ]
                )
            )

    def is_visible(self) -> bool:
        page = self.context.get("self")
        if not isinstance(page, Page):
            return False

        return bool(self.useful_links or self.child_pages)

    def get_part_context(self) -> dict:
        context = super().get_part_context()

        useful_links = []
        for link in self.useful_links:
            useful_links.append(
                {
                    "title": link.value["title"],
                    "url": link.block.get_url(link.value),
                }
            )

        child_page_links = [
            {
                "title": child_page.title,
                "url": child_page.get_url(),
            }
            for child_page in self.child_pages
        ]

        context.update(
            title=self.title,
            useful_links=useful_links + child_page_links,
        )
        return context


class SpotlightPage(SidebarPart):
    template_name = "tags/sidebar/parts/spotlight.html"

    def is_visible(self) -> bool:
        page = self.context.get("self")
        if not isinstance(page, Page):
            return False

        return bool(getattr(page, "spotlight_page", None))

    def get_part_context(self) -> dict:
        context = super().get_part_context()
        page = self.context.get("self")

        spotlight_page = getattr(page, "spotlight_page", None)
        if not isinstance(spotlight_page, Page):
            return context

        spotlight_page = spotlight_page.specific

        context.update(
            page=spotlight_page,
            url=spotlight_page.get_url(self.request),
            title=getattr(spotlight_page, "title", None),
            excerpt=getattr(spotlight_page, "excerpt", None),
            thumbnail=getattr(spotlight_page, "preview_image", None),
        )

        return context


class DiscoverPage(SidebarPart):
    template_name = "tags/sidebar/parts/site_alert.html"

    def is_visible(self) -> bool:
        page = self.context.get("self")
        if not flag_is_active(self.request, flags.PF_DISCOVER):
            return False
        if isinstance(page, HomePage):
            return True

    def get_part_context(self) -> dict:
        context = super().get_part_context()

        context.update(
            banner_text="New 'discover people' page is available!",
            banner_link=reverse("people-discover"),
        )
        return context


@register.inclusion_tag("tags/sidebar.html", takes_context=True)
def sidebar(context):
    sections: list[SidebarSection] = [
        SidebarSection(
            title="Alerts",
            parts=[SiteAlert],
            context=context,
        ),
        SidebarSection(
            title="Primary page actions",
            parts=[
                Bookmark,
                Comment,
                Share,
            ],
            context=context,
            template_name="tags/sidebar/sections/primary_page_actions.html",
        ),
        SidebarSection(
            title="Secondary page actions",
            parts=[
                DiscoverPage,
                UsefulLinks,
                SpotlightPage,
                YourBookmarks,
                QuickLinks,
                GiveFeedback,
            ],
            context=context,
        ),
    ]
    return {"sections": [section for section in sections if section.is_visible()]}
