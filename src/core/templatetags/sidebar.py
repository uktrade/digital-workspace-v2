from typing import Type

from django import template
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.safestring import SafeString
from waffle import flag_is_active
from wagtail.models import Page

from core import flags
from core.models.models import SiteAlertBanner
from home.models import HomePage, QuickLink
from interactions.services import bookmarks as bookmarks_service


register = template.Library()


class SidebarPart:
    template_name: str
    context: dict

    def __init__(self, context: dict):
        self.context = context

    def is_visible(self) -> bool:
        """
        Decide if this part should be visible on the current page.
        """
        return True

    def get_part_context(self):
        """
        Build the context to pass into the template.
        """
        return {}

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

    def get_section_context(self):
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

    def __init__(self, context: dict):
        super().__init__(context)
        self.current_alert = SiteAlertBanner.objects.filter(activated=True).first()

    def is_visible(self, *args, **kwargs):
        page = self.context.get("self")
        if isinstance(page, HomePage) and self.current_alert:
            return True
        return False

    def get_part_context(self):
        return {
            "banner_text": self.current_alert.banner_text,
            "banner_link": self.current_alert.banner_link,
        }


class GiveFeedback(SidebarPart):
    template_name = "tags/sidebar/parts/feedback.html"

    title = "Give feedback"
    description = "Did you find what you were looking for?"

    def is_visible(self):
        request = self.context["request"]
        if not flag_is_active(request, flags.NEW_SIDEBAR):
            return False
        page = self.context.get("self")
        if isinstance(page, HomePage):
            return False
        return True

    def get_part_context(self):
        return {
            "title": self.title,
            "description": self.description,
        }


class YourBookmarks(SidebarPart):
    template_name = "interactions/bookmark_card.html"

    def is_visible(self):
        page = self.context.get("self")
        if isinstance(page, HomePage):
            return True
        return False

    def get_part_context(self):
        return {
            "user": self.context.get("user"),
        }


class Bookmark(SidebarPart):
    template_name = "tags/sidebar/parts/bookmark.html"

    def is_visible(self):
        request = self.context["request"]

        if not flag_is_active(request, flags.NEW_SIDEBAR):
            return False

        page = self.context.get("self")
        if isinstance(page, HomePage):
            return False

        return isinstance(page, Page)

    def get_part_context(self):
        user = self.context.get("user")
        page = self.context.get("self")
        is_bookmarked = bookmarks_service.is_page_bookmarked(user, page)
        post_url = reverse("interactions:bookmark")
        is_new_sidebar_enabled = flag_is_active(
            self.context["request"],
            flags.NEW_SIDEBAR,
        )
        return {
            "post_url": post_url,
            "user": user,
            "page": page,
            "is_bookmarked": is_bookmarked,
            "csrf_token": self.context["csrf_token"],
            "is_new_sidebar_enabled": is_new_sidebar_enabled,
        }


class QuickLinks(SidebarPart):
    template_name = "tags/sidebar/parts/quick_links.html"

    def is_visible(self):
        page = self.context.get("self")
        if isinstance(page, HomePage):
            return True
        return False

    def get_part_context(self):
        request = self.context["request"]
        return {
            "quick_links": [
                {
                    "url": obj.link_to.get_url(request),
                    "text": obj.title,
                }
                for obj in QuickLink.objects.all().order_by("result_weighting", "title")
            ],
        }


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
            ],
            context=context,
            template_name="tags/sidebar/sections/primary_page_actions.html",
        ),
        SidebarSection(
            title="Secondary page actions",
            parts=[
                YourBookmarks,
                QuickLinks,
                GiveFeedback,
            ],
            context=context,
        ),
    ]
    return {"sections": [section for section in sections if section.is_visible()]}
