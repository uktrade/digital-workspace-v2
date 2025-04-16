from django import template

from interactions.services import bookmarks as bookmarks_service


register = template.Library()


@register.inclusion_tag("interactions/bookmark_list.html")
def bookmark_list(user, limit: int | None = None):
    bookmarks = bookmarks_service.get_bookmarks(user)

    if limit:
        bookmarks = bookmarks[:limit]

    return {"bookmarks": bookmarks}
