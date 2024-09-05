from django import template

from news.models import NewsPage


register = template.Library()


@register.simple_tag
def page_to_card(page: NewsPage):
    card_dict = {
        "title": page.title,
        "thumbnail": page.preview_image,
        "url": page.url,
        "date": page.last_published_at,
        "comment_count": page.comment_count,
        "excerpt": page.excerpt,
        "hide_shadow": True,
        "ribbon_text": None,
        "template": "dwds/components/engagement_card.html",
    }
    if hasattr(page, "ribbon_text"):
        card_dict["ribbon_text"] = page.ribbon_text
    # TODO: Add event logic here
    return card_dict


@register.simple_tag
def pages_to_cards(pages: list[NewsPage]):
    return [page_to_card(page) for page in pages]
