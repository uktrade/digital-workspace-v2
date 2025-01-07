def get_recent_page_views(user, *, limit=10, exclude_pages=None):
    from .models import RecentPageView

    qs = RecentPageView.objects.select_related("page").filter(user=user)

    if exclude_pages:
        qs = qs.exclude(page__in=exclude_pages)

    return qs[:limit]


def get_updated_pages(user):
    from .models import RecentPageView

    for page_view in RecentPageView.objects.filter(
        user=user, page__last_published_at__isnull=False
    ):
        if page_view.updated_at < page_view.page.last_published_at:  # type: ignore #
            yield page_view.page
