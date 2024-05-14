from waffle import flag_is_active

from core.models import FeatureFlag


def get_all_feature_flags(request):
    return {
        flag.name: flag_is_active(request, flag.name)
        for flag in FeatureFlag.objects.all()
    }
