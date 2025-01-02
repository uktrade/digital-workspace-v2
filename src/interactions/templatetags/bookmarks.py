from django import template
from django.urls import reverse
from wagtail.models import Page

from interactions.services import bookmarks as bookmarks_service


register = template.Library()


@register.inclusion_tag("interactions/bookmark_page_input.html")
def bookmark_page_input(user, page):
    if page is None:
        return {}

    if not isinstance(page, Page):
        return {}

    is_bookmarked = bookmarks_service.is_page_bookmarked(user, page)

    return {
        "post_url": reverse("interactions:bookmark"),
        "user": user,
        "page": page,
        "is_bookmarked": is_bookmarked,
    }


@register.inclusion_tag("interactions/bookmark_list.html")
def bookmark_list(user, limit: int | None = None):
    bookmarks = bookmarks_service.get_bookmarks(user)

    if limit:
        bookmarks = bookmarks[:limit]

    return {"bookmarks": bookmarks}
