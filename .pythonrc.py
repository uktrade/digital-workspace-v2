from pprint import pprint

import peoplefinder.legacy_models as pf_legacy_models
import peoplefinder.models as pf_models
from user.models import User


def make_superuser(email):
    user = get_user(email)
    user.is_staff = True
    user.is_superuser = True
    user.save()


def get_user(email):
    return User.objects.get(email=email)
