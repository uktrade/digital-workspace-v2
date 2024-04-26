from waffle import flag_is_active

from core.models import FeatureFlag


def set_seen_cookie_banner(request, response):
    if not request.COOKIES.get("seen_cookie_banner"):
        response.set_cookie(
            "seen_cookie_banner",
            1,
            secure=False,
        )


def get_all_feature_flags(request):
    return {
        flag.name: flag_is_active(request, flag.name)
        for flag in FeatureFlag.objects.all()
    }
