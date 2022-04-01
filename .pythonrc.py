from pprint import pprint

import peoplefinder.legacy_models as pf_legacy_models
import peoplefinder.models as pf_models
from user.models import User


def make_superuser(email):
    user = User.objects.get(email=email)
    user.is_staff = True
    user.is_superuser = True
    user.save()
