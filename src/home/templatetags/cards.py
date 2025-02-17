from django import template
from django.template.loader import render_to_string
from django.utils.safestring import SafeString

from events.models import EventPage
from events.utils import (
    get_event_datetime_display_string,
)
from networks.models import Network
from news.models import NewsPage


register = template.Library()


def page_to_display_context(page: NewsPage | EventPage, hide_updated: bool = False):
    context = {
        "title": page.title,
        "thumbnail": page.preview_image,
        "url": page.url,
        "excerpt": page.excerpt,
        "ribbon_text": None,
    }

    if hasattr(page, "ribbon_text"):
        context["ribbon_text"] = page.ribbon_text

    if issubclass(type(page), NewsPage):
        context.update(
            created_date=page.first_published_at,
            comment_count=page.comment_count,
            reaction_count=page.reaction_count,
            allow_comments=page.allow_comments,
            allow_reactions=page.allow_reactions,
        )
        if not hide_updated:
            context.update(
                updated_date=page.last_published_at,
            )

    if issubclass(type(page), EventPage):
        context.update(post_title=get_event_datetime_display_string(page))

    return context


class RenderableComponent:
    def __init__(self, template_name: str, context: dict):
        self.template_name = template_name
        self.context = context

    def render(self, *args, **kwargs) -> SafeString:
        return render_to_string(self.template_name, self.context)

    __str__ = render
    __html__ = render


@register.simple_tag
def page_to_engagement(
    page: NewsPage | EventPage | Network, hide_updated: bool = False
) -> SafeString:
    return RenderableComponent(
        "dwds/components/engagement.html",
        page_to_display_context(page, hide_updated=hide_updated),
    )


@register.simple_tag
def pages_to_engagement(pages: list[NewsPage | EventPage]) -> list[RenderableComponent]:
    return [page_to_engagement(page) for page in pages]


@register.simple_tag
def page_to_one_up(page: NewsPage | EventPage) -> SafeString:
    return RenderableComponent(
        "dwds/components/one_up.html",
        page_to_display_context(page),
    )
