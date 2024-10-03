from django import template

from events.models import EventPage
from events.utils import get_event_start_date, get_event_start_time
from news.models import NewsPage


register = template.Library()


@register.simple_tag
def page_to_card(page: NewsPage | EventPage, hide_shadow: bool = False):
    card_dict = {
        "title": page.title,
        "thumbnail": page.preview_image,
        "url": page.url,
        "excerpt": page.excerpt,
        "hide_shadow": hide_shadow,
        "grid": False,
        "blue_bg": False,
        "show_hr": False,
        "ribbon_text": None,
        "template": "dwds/components/engagement_card.html",
    }

    if hasattr(page, "ribbon_text"):
        card_dict["ribbon_text"] = page.ribbon_text

    if issubclass(type(page), NewsPage):
        card_dict.update(
            created_date=page.first_published_at,
            updated_date=page.last_published_at,
            comment_count=page.comment_count,
        )

    if issubclass(type(page), EventPage):
        card_dict.update(
            post_title_date=get_event_start_date(page),
            post_title_time=get_event_start_time(page),
        )

    return card_dict


@register.simple_tag
def pages_to_cards(pages: list[NewsPage | EventPage], hide_shadow: bool = False):
    return [page_to_card(page, hide_shadow=hide_shadow) for page in pages]
