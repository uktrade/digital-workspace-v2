from django.db.models.query import QuerySet

from content.models import BasePage
from interactions.models import Bookmark
from user.models import User


def toggle_bookmark(user: User, page: BasePage) -> None:
    bookmark = not is_page_bookmarked(user, page)
    if bookmark:
        Bookmark.objects.get_or_create(user=user, page=page)
    else:
        Bookmark.objects.get(user=user, page=page).delete()


def remove_bookmark(pk: str, user: User) -> None:
    Bookmark.objects.get(pk=pk, user=user).delete()


def get_bookmarks(user: User) -> QuerySet[Bookmark]:
    return Bookmark.objects.select_related("page").filter(user=user)


def is_page_bookmarked(user: User, page: BasePage) -> bool:
    return get_bookmarks(user).filter(page=page).exists()
