from django import template
from django.templatetags.static import static
from django.urls import reverse
from wagtail.models import Page

from interactions import is_page_bookmarked, get_bookmarks


register = template.Library()


@register.inclusion_tag("interactions/bookmark_page.html")
def bookmark_page(user, page):
    if page is None:
        return {}

    if not isinstance(page, Page):
        return {}

    is_bookmarked = is_page_bookmarked(user, page)

    icon = "bookmark.svg" if is_bookmarked else "bookmark-outline.svg"

    return {
        "img_src": static(f"interactions/{icon}"),
        "post_url": reverse("interactions:bookmark"),
        "user": user,
        "page": page,
        "is_bookmarked": is_bookmarked,
    }


@register.inclusion_tag("interactions/bookmark_list.html")
def bookmark_list(user, limit: int | None = None):
    bookmarks = get_bookmarks(user)

    if limit:
        bookmarks = bookmarks[:limit]

    return {"bookmarks": bookmarks}
