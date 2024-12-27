from django import template
from django.template.loader import render_to_string
from django.utils.safestring import SafeString

from home.models import HomePage


register = template.Library()


class SidebarPart:
    template_name: str
    context: dict

    def __init__(self, context):
        self.context = context

    def is_visible(self, context) -> bool:
        return True

    def get_part_context(self):
        return {}

    def render(self, *args, **kwargs) -> SafeString:
        return render_to_string(self.template_name, self.get_part_context())

    __str__ = render
    __html__ = render


class SidebarSection:
    title: str
    parts: list[SidebarPart] = []

    def __init__(self, title: str, parts: list[SidebarPart]):
        self.title = title
        self.parts = parts


class GiveFeedback(SidebarPart):
    template_name = "tags/sidebar/feedback.html"

    title = "Give feedback"
    description = "Did you find what you were looking for?"

    def is_visible(self, *args, **kwargs):
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

    def is_visible(self, *args, **kwargs):
        page = self.context.get("self")
        if isinstance(page, HomePage):
            return True
        return False

    def get_part_context(self):
        return {
            "user": self.context.get("user"),
        }


@register.inclusion_tag("tags/sidebar.html", takes_context=True)
def sidebar(context):
    sections: list[SidebarSection] = [
        SidebarSection(
            title="Primary page actions",
            parts=[],
        ),
        SidebarSection(
            title="Secondary page actions",
            parts=[
                GiveFeedback(context=context),
                YourBookmarks(context=context),
            ],
        ),
    ]
    return {"sections": sections}
