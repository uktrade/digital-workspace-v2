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
    user: User,
    team: Team,
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


def check_visible_button(state, test_url, button_title, codename):
    response = state.client.get(test_url)
    assert response.status_code == 200
    assert button_title not in response.content
    soup = BeautifulSoup(response.content, features="html.parser")
    buttons = soup.find_all('a')
    button_len = len(buttons)

    edit_team_perm = Permission.objects.get(
        codename=codename
    )
    state.user.user_permissions.add(edit_team_perm)

    response = state.client.get(test_url)
    assert response.status_code == 200
    assert button_title in response.content
    soup = BeautifulSoup(response.content, features="html.parser")
    buttons = soup.find_all('a')
    assert len(buttons) == button_len + 1


def check_permission(state, view_url, codename):
    response = state.client.get(view_url)
    assert response.status_code == 403

    edit_profile_perm = Permission.objects.get(
        codename=codename
    )
    state.user.user_permissions.add(edit_profile_perm)
    state.user.save()

    response = state.client.get(view_url)
    assert response.status_code == 200


def test_edit_profile_group(state):
    team = TeamFactory()
    user = UserFactory()
    person = PersonService().create_user_profile(user)

    client = Client()
    client.force_login(user)

    return State(client=client, person=person,  team=team, user=user)


def test_edit_profile_permission(state):
    edit_profile_url = reverse(
        "profile-edit",
        kwargs={
            'profile_slug': state.person.slug,
        }
    )
    response = state.client.get(edit_profile_url)
    assert response.status_code == 403
    call_command("create_people_finder_groups")
    edit_profile_group = Group.objects.get(
        name='Profile Editors'
    )
    state.user.groups.add(edit_profile_group)

    response = state.client.get(edit_profile_url)
    assert response.status_code == 403

    edit_profile_perm = Permission.objects.get(
        codename='edit_profile'
    )
    state.user.user_permissions.add(edit_profile_perm)
    state.user.save()

    response = state.client.get(edit_profile_url)
    assert response.status_code == 200


def test_edit_profile_permission(state):
    edit_profile_url = reverse(
        "profile-edit",
        kwargs={
            'profile_slug': state.person.slug,
        }
    )
    check_permission(state, edit_profile_url, 'edit_profile')


def test_edit_team_permission(state):
    edit_url = reverse(
        "team-edit",
        kwargs={
            'slug': state.team.slug,
        }
    )
    check_permission(state, edit_url, 'change_team')


def test_add_sub_team_permission(state):
    add_url = reverse(
        "team-add-new-subteam",
        kwargs={
            'slug': state.team.slug,
        }
    )
    check_permission(state, add_url, 'add_team')


def test_delete_team_permission(state):
    add_url = reverse(
        "team-delete",
        kwargs={
            'slug': state.team.slug,
        }
    )
    check_permission(state, add_url, 'delete_team')


def test_edit_profile_visible_permission(state):
    view_url = reverse(
        "profile-view",
        kwargs={
            'profile_slug': state.person.slug,
        }
    )
    check_visible_button(state, view_url, b"Edit profile", "edit_profile")


def test_edit_team_visible_permission(state):
    view_url = reverse(
        "team-view",
        kwargs={
            'slug': state.team.slug,
        }
    )
    check_visible_button(state, view_url, b"Edit team", "change_team")


def test_delete_team_visible_permission(state):
    view_url = reverse(
        "team-view",
        kwargs={
            'slug': state.team.slug,
        }
    )
    check_visible_button(state, view_url, b"Delete team", "delete_team")


def test_create_sub_team_visible_permission(state):
    view_url = reverse(
        "team-view",
        kwargs={
            'slug': state.team.slug,
        }
    )
    check_visible_button(state, view_url, b"Add new sub-team", "add_team")

def test_edit_team_permission(state):
    # TODO implement
    pass
