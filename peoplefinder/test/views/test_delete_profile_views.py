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


def check_button_is_visible(content, button_title) -> bool:
    breakpoint()
    soup = BeautifulSoup(content, features="html.parser")

    # Find all anchors with GDS 'buttons'
    buttons = soup.find_all("a", class_="govuk-button")

    assert button_title in str(buttons)


def test_delete_profile_permission(state):
    view_url = reverse(
        "profile-view",
        kwargs={
            'profile_slug': state.person.slug,
        }
    )

    edit_team_perm = Permission.objects.get(
        codename="delete_profile"
    )
    state.user.user_permissions.add(edit_team_perm)

    response = state.client.get(view_url)
    assert response.status_code == 200

    check_button_is_visible(response.content, "Delete profile")
