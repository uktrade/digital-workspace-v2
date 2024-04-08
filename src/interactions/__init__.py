def get_recent_page_views(user, limit=10):
    from .models import RecentPageView

    return RecentPageView.objects.select_related("page").filter(user=user)[:limit]


def get_bookmarks(user):
    from .models import Bookmark

    return Bookmark.objects.select_related("page").filter(user=user)


def is_page_bookmarked(user, page):
    return get_bookmarks(user).filter(page=page).exists()
