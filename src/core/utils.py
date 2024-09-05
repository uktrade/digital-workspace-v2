from datetime import time

from waffle import flag_is_active

from core.models import FeatureFlag


def get_all_feature_flags(request):
    return {
        flag.name: flag_is_active(request, flag.name)
        for flag in FeatureFlag.objects.all()
    }


def format_time(time_obj: time) -> str:
    """
    Build a time string that shows the needed information.

    Returns:
     - If there are minutes on the hour: `10:30` -> `10:30am`
     - If there are not minutes on the hour: `10:00` -> `10am`

    """
    if time_obj.minute == 0:
        return time_obj.strftime("%-I%p").lstrip("0").lower()
    return time_obj.strftime("%-I:%M%p").lstrip("0").lower()
