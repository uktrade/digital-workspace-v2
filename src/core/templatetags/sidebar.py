from django import template
from django.template.loader import render_to_string
from django.utils.safestring import SafeString

from core.models.models import SiteAlertBanner
from home.models import HomePage, QuickLink


register = template.Library()


class SidebarPart:
    template_name: str
    context: dict

    def __init__(self, context):
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

    def __init__(self, title: str, parts: list[SidebarPart]):
        self.title = title
        self.parts = parts


class SiteAlert(SidebarPart):
    template_name = "tags/sidebar/site_alert.html"

    def __init__(self, context):
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
    template_name = "tags/sidebar/feedback.html"

    title = "Give feedback"
    description = "Did you find what you were looking for?"

    def is_visible(self):
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

class Bookmarks(SidebarPart):
    template_name = "interactions/bookmark_wrapper.html"

    def is_visible(self):
        page = self.context.get("self")
        if isinstance(page, HomePage):
            return False
        return True

    def get_part_context(self):
        return {
            "user": self.context.get("user"),
            "page": self.context.get("self"),
            "csrf_token": self.context["csrf_token"],
        }

class QuickLinks(SidebarPart):
    template_name = "tags/sidebar/quick_links.html"

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
            parts=[SiteAlert(context=context)],
        ),
        SidebarSection(
            title="Primary page actions",
            parts=[
                Bookmarks(context=context),
            ],
        ),
        SidebarSection(
            title="Secondary page actions",
            parts=[
                YourBookmarks(context=context),
                QuickLinks(context=context),
                GiveFeedback(context=context),
            ],
        ),
    ]
    return {"sections": sections}
