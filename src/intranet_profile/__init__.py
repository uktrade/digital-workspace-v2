from .models import IntranetProfile


def create_intranet_profile(user):
    if hasattr(user, "intranet"):
        return IntranetProfile.objects.create(user=user)


def get_recent_page_views(user, limit=10):
    return user.intranet.recent_page_views.all()[:limit]
