def get_recent_page_views(user, limit=10):
    from .models import RecentPageView

    return RecentPageView.objects.select_related("page").filter(user=user)[:limit]


def get_bookmarks(user):
    from .models import Bookmark

    return Bookmark.objects.select_related("page").filter(user=user)


def is_page_bookmarked(user, page):
    return get_bookmarks(user).filter(page=page).exists()


def get_updated_pages(user):
    from .models import RecentPageView

    for page_view in RecentPageView.objects.filter(
        profile=user.intranet, page__last_published_at__isnull=False
    ):
        if page_view.updated_at > page_view.page.last_published_at:
            yield page_view.page
