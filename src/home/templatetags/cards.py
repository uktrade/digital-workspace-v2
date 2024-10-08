from django import template
from django.template.loader import render_to_string
from django.utils.safestring import SafeString

from events.models import EventPage
from events.utils import get_event_date, get_event_time
from news.models import NewsPage


register = template.Library()


def page_to_display_context(page: NewsPage | EventPage):
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
            updated_date=page.last_published_at,
            comment_count=page.comment_count,
        )

    if issubclass(type(page), EventPage):
        context.update(
            post_title_date=get_event_date(page),
            post_title_time=get_event_time(page),
        )

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
def page_to_engagement(page: NewsPage | EventPage) -> SafeString:
    return RenderableComponent(
        "dwds/components/engagement.html",
        page_to_display_context(page),
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
