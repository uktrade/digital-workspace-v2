from django import template
from django.urls import reverse
from waffle import flag_is_active
from wagtail.models import Page

from core import flags
from events.models import EventsHome
from home.models import HomePage
from interactions.services import bookmarks as bookmarks_service
from networks.models import NetworksHome


register = template.Library()


# TODO: Remove `bookmark_page_input` once `new_sidebar` flag is removed
@register.inclusion_tag("interactions/bookmark_page_input.html")
def bookmark_page_input(user, page, request):
    if flag_is_active(request, flags.NEW_SIDEBAR):
        return {}

    if page is None:
        return {}

    if not isinstance(page, Page):
        return {}

    if isinstance(page, (HomePage, EventsHome, NetworksHome)):
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
