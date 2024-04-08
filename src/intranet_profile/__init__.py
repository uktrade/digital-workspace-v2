def create_intranet_profile(user):
    from .models import IntranetProfile

    if hasattr(user, "intranet"):
        return user.intranet

    return IntranetProfile.objects.create(user=user)


def get_recent_page_views(user, limit=10):
    return user.intranet.recent_page_views.all()[:limit]


def get_bookmarks(user):
    return user.intranet.bookmarks.all()


def is_page_bookmarked(user, page):
    return user.intranet.bookmarks.filter(pk=page.pk).exists()


def get_updated_pages(user):
    from .models import RecentPageView

    pages = []
    for page_view in RecentPageView.objects.filter(profile=user.intranet):
        if (
            page_view.page.last_published_at is not None
            and page_view.last_viewed_at > page_view.page.last_published_at
        ):
            pages.append(page_view.page)
    return pages
