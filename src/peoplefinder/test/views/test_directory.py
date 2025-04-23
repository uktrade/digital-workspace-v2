import pytest
import datetime as dt
from waffle.testutils import override_flag
from core.models.models import FeatureFlag
from peoplefinder.models import Person
from django.test.client import Client
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_discover_with_flag_inactive(normal_user):
    client = Client()
    url = reverse("people-discover")

    # Request discover page as normal_user when the flag is inactive
    client.force_login(normal_user)
    FeatureFlag.objects.create(name="pf_discover")

    with override_flag("pf_discover", active=False):
        response = client.get(url)
        assert response.status_code == 302
        assert response["Location"] == reverse("people-directory")


def test_discover_with_flag_active(normal_user, another_normal_user):
    # Get user profiles
    john_profile = Person.objects.get(user=normal_user)
    jane_profile = Person.objects.get(user=another_normal_user)

    client = Client()
    url = reverse("people-discover")

    # Request discover page as normal_user when the flag is active
    client.force_login(normal_user)
    FeatureFlag.objects.create(name="pf_discover")

    with override_flag("pf_discover", active=True):
        response = client.get(url)

        assert response.status_code == 200
        assert (
            f"{john_profile.preferred_first_name} {john_profile.last_name}"
            in response.content.decode()
        )
        assert (
            f"{jane_profile.preferred_first_name} {jane_profile.last_name}"
            in response.content.decode()
        )

        # Check normal_user is not able to see users that were deactivated more than 90 days ago
        jane_profile.is_active = False
        jane_profile.became_inactive = dt.datetime.now() - dt.timedelta(days=100)
        jane_profile.save()

        response = client.get(url)

        assert response.status_code == 200
        assert (
            f"{john_profile.preferred_first_name} {john_profile.last_name}"
            in response.content.decode()
        )
        assert (
            f"{jane_profile.preferred_first_name} {jane_profile.last_name}"
            not in response.content.decode()
        )
