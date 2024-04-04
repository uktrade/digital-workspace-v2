def create_intranet_profile(user):
    from .models import IntranetProfile

    if hasattr(user, "intranet"):
        return user.intranet

    return IntranetProfile.objects.create(user=user)


def get_recent_page_views(user, limit=10):
    return user.intranet.recent_page_views.all()[:limit]


def is_page_bookmarked(user, page):
    return user.intranet.bookmarks.filter(pk=page.pk).exists()
