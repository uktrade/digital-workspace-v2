from dataclasses import dataclass

import pytest
from bs4 import BeautifulSoup
from django.contrib.auth.models import Group, Permission
from django.core.management import call_command
from django.test.client import Client
from django.urls import reverse
from pytest_django.asserts import assertContains

from peoplefinder.forms.profile import ProfileForm
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
    user.save()
    person = PersonService().create_user_profile(user)
    client = Client()
    client.force_login(user)
    return State(client=client, person=person, team=team, user=user)


def check_visible_button(state, test_url, button_title, codename):
    response = state.client.get(test_url)
    assert response.status_code == 200
    assert button_title not in response.content
    soup = BeautifulSoup(response.content, features="html.parser")
    buttons = soup.find_all("a")
    button_len = len(buttons)

    edit_team_perm = Permission.objects.get(codename=codename)
    state.user.user_permissions.add(edit_team_perm)

    response = state.client.get(test_url)
    assert response.status_code == 200
    assert button_title in response.content
    soup = BeautifulSoup(response.content, features="html.parser")
    buttons = soup.find_all("a")
    assert len(buttons) == button_len + 1


def check_permission(state, view_url, codename):
    response = state.client.get(view_url)
    assert response.status_code == 403

    edit_profile_perm = Permission.objects.get(codename=codename)
    state.user.user_permissions.add(edit_profile_perm)
    state.user.save()

    response = state.client.get(view_url)
    assert response.status_code == 200


def test_edit_profile(state):
    edit_profile_url = reverse(
        "profile-edit",
        kwargs={
            "profile_slug": state.person.slug,
        },
    )
    response = state.client.get(edit_profile_url)
    assert response.status_code == 200


def test_edit_team_permission(state):
    edit_url = reverse(
        "team-edit",
        kwargs={
            "slug": state.team.slug,
        },
    )
    check_permission(state, edit_url, "change_team")


def test_add_sub_team_permission(state):
    add_url = reverse(
        "team-add-new-subteam",
        kwargs={
            "slug": state.team.slug,
        },
    )
    check_permission(state, add_url, "add_team")


def test_delete_team_permission(state):
    add_url = reverse(
        "team-delete",
        kwargs={
            "slug": state.team.slug,
        },
    )
    check_permission(state, add_url, "delete_team")


def test_edit_profile_visible(state):
    view_url = reverse(
        "profile-view",
        kwargs={
            "profile_slug": state.person.slug,
        },
    )
    response = state.client.get(view_url)
    assertContains(response, "Edit profile", html=True)


def test_edit_team_visible_permission(state):
    view_url = reverse(
        "team-view",
        kwargs={
            "slug": state.team.slug,
        },
    )
    check_visible_button(state, view_url, b"Edit team", "change_team")


def test_delete_team_visible_permission(state):
    view_url = reverse(
        "team-view",
        kwargs={
            "slug": state.team.slug,
        },
    )
    check_visible_button(state, view_url, b"Delete team", "delete_team")


def test_create_sub_team_visible_permission(state):
    view_url = reverse(
        "team-view",
        kwargs={
            "slug": state.team.slug,
        },
    )
    check_visible_button(state, view_url, b"Add new sub-team", "add_team")


def test_team_log_visible_permission(state):
    view_url = reverse(
        "team-view",
        kwargs={
            "slug": state.team.slug,
        },
    )
    response = state.client.get(view_url)
    assert response.status_code == 200
    title = b"Audit log"
    assert title not in response.content
    soup = BeautifulSoup(response.content, features="html.parser")

    log_detail = soup.find_all(attrs={"data-module": "govuk-details"})
    log_detail_len = len(log_detail)

    team_admin_group = Group.objects.get(name="Team Admin")  # /PS-IGNORE
    state.user.groups.add(team_admin_group)

    response = state.client.get(view_url)
    assert response.status_code == 200
    assert title in response.content
    soup = BeautifulSoup(response.content, features="html.parser")
    log_detail = soup.find_all(attrs={"data-module": "govuk-details"})
    assert len(log_detail) == log_detail_len + 1


def test_self_profile_log_visible_permission(state):
    view_url = reverse(
        "profile-view",
        kwargs={
            "profile_slug": state.person.slug,
        },
    )
    response = state.client.get(view_url)
    assert response.status_code == 200
    title = b"Audit log"
    assert title in response.content


def test_profile_log_visible_permission(state):
    other_user = UserFactory(username="other_user", legacy_sso_user_id="other_user")
    other_user.save()
    other_person = PersonService().create_user_profile(other_user)

    view_url = reverse(
        "profile-view",
        kwargs={
            "profile_slug": other_person.slug,
        },
    )
    response = state.client.get(view_url)
    assert response.status_code == 200
    title = b"Audit log"
    assert title not in response.content
    soup = BeautifulSoup(response.content, features="html.parser")

    log_detail = soup.find_all(attrs={"data-module": "govuk-details"})
    log_detail_len = len(log_detail)

    view_log_perm = Permission.objects.get(codename="view_auditlog")
    state.user.user_permissions.add(view_log_perm)

    response = state.client.get(view_url)
    assert response.status_code == 200
    assert title in response.content
    soup = BeautifulSoup(response.content, features="html.parser")
    log_detail = soup.find_all(attrs={"data-module": "govuk-details"})

    assert len(log_detail) == log_detail_len + 2


def test_profile_detail_view(state):
    view_url = reverse(
        "profile-view",
        kwargs={
            "profile_slug": state.person.slug,
        },
    )
    response = state.client.get(view_url)
    assert response.status_code == 200


def test_profile_edit_view(state):
    view_url = reverse(
        "profile-edit",
        kwargs={
            "profile_slug": state.person.slug,
        },
    )

    response = state.client.get(view_url)

    assert response.status_code == 200
    assert state.person.primary_phone_number is None

    form = ProfileForm({"primary_phone_number": "07000"}, instance=state.person)
    form.is_valid()

    # Need to remove items with no value with cleaned data in order that "POST" will work
    payload = {}
    for key, value in form.cleaned_data.items():
        if value:
            payload[key] = value

    response = state.client.post(view_url, payload)

    assert response.status_code == 200
    assert state.person.primary_phone_number == "07000"


def test_user_admin_no_superuser(state):
    PersonService.update_groups_and_permissions(
        person=state.person,
        is_person_admin=False,
        is_team_admin=False,
        is_superuser=False,
    )
    view_url = reverse(
        "profile-edit",
        kwargs={
            "profile_slug": state.person.slug,
        },
    )

    response = state.client.get(view_url)

    assert response.status_code == 200

    soup = BeautifulSoup(response.content, features="html.parser")

    assert not soup.find(lambda tag: tag.name == "span" and "Permissions" in tag.text)


def test_user_admin_with_superuser(state):
    PersonService.update_groups_and_permissions(
        person=state.person,
        is_person_admin=False,
        is_team_admin=False,
        is_superuser=True,
    )
    view_url = reverse(
        "profile-edit",
        kwargs={
            "profile_slug": state.person.slug,
        },
    )

    response = state.client.get(view_url)

    assert response.status_code == 200

    soup = BeautifulSoup(response.content, features="html.parser")

    assert soup.find(lambda tag: tag.name == "span" and "Permissions" in tag.text)


def test_user_admin_no_superuser_but_team_person_admin(state):
    PersonService.update_groups_and_permissions(
        person=state.person,
        is_person_admin=True,
        is_team_admin=True,
        is_superuser=False,
    )
    view_url = reverse(
        "profile-edit",
        kwargs={
            "profile_slug": state.person.slug,
        },
    )

    response = state.client.get(view_url)

    assert response.status_code == 200

    soup = BeautifulSoup(response.content, features="html.parser")

    assert not soup.find(lambda tag: tag.name == "span" and "Permissions" in tag.text)


class TestProfileUpdateUserView:
    def _update_user(self, client, profile, new_user):
        return client.post(
            reverse("profile-update-user", kwargs={"profile_slug": profile.slug}),
            {"username": new_user.username},
        )

    def test_swap_user(self, normal_user, state):
        john = normal_user
        john_profile = john.profile
        jane = state.user
        jane_profile = jane.profile

        assert john.profile == john_profile

        self._update_user(state.client, jane.profile, john)

        john.refresh_from_db()
        jane.refresh_from_db()

        assert john.profile == jane_profile
        assert not hasattr(jane, "profile")
