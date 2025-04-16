import pytest
import datetime as dt
from django.contrib.auth.models import Permission

from peoplefinder.models import Person
from peoplefinder.services import directory as directory_service
from user.models import User

pytestmark = pytest.mark.django_db


def test_get_people_as_normal_user(normal_user, another_normal_user):
    # Get user profiles
    john_profile = Person.objects.get(user=normal_user)
    jane_profile = Person.objects.get(user=another_normal_user)

    # Test case 1:

    # Jane became inactive 80 days ago
    jane_profile.is_active = False
    jane_profile.became_inactive = dt.datetime.now() - dt.timedelta(days=80)
    jane_profile.save()

    people_set = directory_service.get_people(user=normal_user)

    # normal_user is able to see John's profile and Jane's profile
    # as it was deactivated less than 90 days ago
    assert jane_profile in people_set
    assert john_profile in people_set

    # Test case 2:

    # Jane became inactive 100 days ago
    jane_profile.is_active = False
    jane_profile.became_inactive = dt.datetime.now() - dt.timedelta(days=100)
    jane_profile.save()

    people_set = directory_service.get_people(user=normal_user)

    # normal_user is not able to see Jane's profile as it was deactivated
    # more than 90 days ago. John's profile is active and visible.
    assert jane_profile not in people_set
    assert john_profile in people_set


def test_get_people_as_user_with_view_inactive_permission(
    normal_user, another_normal_user
):
    # Get user profiles
    john_profile = Person.objects.get(user=normal_user)
    jane_profile = Person.objects.get(user=another_normal_user)

    # normal_user gets can_view_inactive_profiles permission
    permission = Permission.objects.get(
        codename="can_view_inactive_profiles",
    )
    normal_user.user_permissions.add(permission)

    # Clear permission cache
    # https://docs.djangoproject.com/en/5.1/topics/auth/default/#permission-caching
    normal_user = User.objects.get(pk=normal_user.pk)

    people_set = directory_service.get_people(user=normal_user)

    # Normal user with "can_view_inactive_profiles" permission is able to see John's profile and
    # Jane's profile even though it was deactivated more than 90 days ago
    assert jane_profile in people_set
    assert john_profile in people_set


def test_get_people_as_superuser(normal_user, another_normal_user):
    # Get user profiles
    john_profile = Person.objects.get(user=normal_user)
    jane_profile = Person.objects.get(user=another_normal_user)

    # normal_user becomes superuser
    normal_user.is_superuser = True
    normal_user.save()

    people_set = directory_service.get_people(user=normal_user)

    # Superuser is able to see John's profile and Jane's profile even though it was deactivated
    # more than 90 days ago
    assert jane_profile in people_set
    assert john_profile in people_set
