from pprint import pprint

from user.models import User


def make_superuser(email):
    user = get_user(email)
    user.is_staff = True
    user.is_superuser = True
    user.save()


def get_user(email):
    return User.objects.get(email__startswith=email)
