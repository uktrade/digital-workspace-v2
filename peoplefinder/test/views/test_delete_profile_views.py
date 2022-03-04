import pytest

from bs4 import BeautifulSoup

from dataclasses import dataclass
from django.contrib.auth.models import (
    Group,
    Permission,
)
from django.core.management import call_command
from django.test.client import Client
from django.urls import reverse

from peoplefinder.models import Person, Team
from peoplefinder.services.person import PersonService
from peoplefinder.test.factories import TeamFactory

from user.models import User
from user.test.factories import UserFactory


@dataclass
class State:
    client: Client
    user: User
    team: Team
    person: Person


@pytest.fixture()
def state(db):
    team = Team.objects.all().last()
    if team == None:
        team = TeamFactory()
    user = UserFactory()
    user.is_using_peoplefinder_v2 = True
    user.save()
    person = PersonService().create_user_profile(user)
    client = Client()
    client.force_login(user)
    return State(client=client, person=person,  team=team, user=user)


def button_is_visible(content, id) -> bool:
    soup = BeautifulSoup(content, features="html.parser")

    # Find delete 'button'
    return bool(soup.find("input", {"id": id}))


def test_delete_profile_with_permission(state):
    profile_url = reverse(
        "profile-view",
        kwargs={
            'profile_slug': state.person.slug,
        }
    )

    delete_profile_perm = Permission.objects.get(
        codename="delete_profile"
    )
    state.user.user_permissions.add(delete_profile_perm)

    response = state.client.get(profile_url)
    assert response.status_code == 200

    assert button_is_visible(response.content, "delete-profile")


def test_delete_profile_no_permission(state):
    profile_url = reverse(
        "profile-view",
        kwargs={
            'profile_slug': state.person.slug,
        }
    )

    response = state.client.get(profile_url)
    assert response.status_code == 200

    assert not button_is_visible(response.content, "delete-profile")


def test_delete_profile_view(state):
    profile_url = reverse(
        "profile-delete",
        kwargs={
            'profile_slug': state.person.slug,
        }
    )

    assert Person.objects.filter(pk=state.person.pk).exists()

    response = state.client.post(profile_url)
    assert response.status_code == 302

    assert not Person.objects.filter(pk=state.person.pk).exists()
