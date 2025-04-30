from dataclasses import dataclass

import pytest
from bs4 import BeautifulSoup
from django.contrib.auth.models import Permission
from django.test.client import Client
from django.urls import reverse
from pytest_django.asserts import assertRedirects

from peoplefinder.models import Person, Team
from peoplefinder.services.person import PersonService
from peoplefinder.test.factories import TeamFactory
from peoplefinder.views.profile import CannotDeleteOwnProfileError
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


def button_is_visible(content, id) -> bool:
    soup = BeautifulSoup(content, features="html.parser")

    # Find 'button'
    return bool(soup.find("input", {"id": id}))


def test_user_cannot_view_own_profile_delete_button_with_permission(state):
    profile_url = reverse(
        "profile-view",
        kwargs={
            "profile_slug": state.person.slug,
        },
    )

    delete_person_perm = Permission.objects.get(codename="delete_person")
    state.user.user_permissions.add(delete_person_perm)

    response = state.client.get(profile_url)

    assert response.status_code == 200
    assert not button_is_visible(response.content, "delete-profile")


def test_profile_delete_button_visible_with_permission(state):
    other_user = UserFactory(
        first_name="Other",
        last_name="User",
        email="other.user@test.com",  # /PS-IGNORE
        legacy_sso_user_id=None,
        username="other.user@-1111111@id.test.gov.uk",  # /PS-IGNORE
        sso_contact_email="other.user@test.com",  # /PS-IGNORE
    )
    other_user.save()
    other_person = PersonService().create_user_profile(other_user)

    profile_url = reverse(
        "profile-view",
        kwargs={
            "profile_slug": other_person.slug,
        },
    )

    delete_person_perm = Permission.objects.get(codename="delete_person")
    state.user.user_permissions.add(delete_person_perm)

    response = state.client.get(profile_url)

    assert response.status_code == 200
    assert button_is_visible(response.content, "delete-profile")


def test_profile_delete_button_not_visible_no_permission(state):
    profile_url = reverse(
        "profile-view",
        kwargs={
            "profile_slug": state.person.slug,
        },
    )

    response = state.client.get(profile_url)

    assert response.status_code == 200
    assert not button_is_visible(response.content, "delete-profile")


def test_delete_confirmation_view(state):
    view_url = reverse(
        "delete-confirmation",
    )

    # Test with no session variable view redirects
    response = state.client.get(view_url, follow=True)
    next_url, status_code = response.redirect_chain[0]

    assert status_code == 302
    assert next_url == reverse("people-home")

    # Test user with session variable gives 200 response - no redirection
    session = state.client.session
    session["profile_name"] = state.person.full_name
    session.save()

    response = state.client.get(view_url)

    assert response.status_code == 200

    # Check confirmation message
    full_name = session["profile_name"]
    soup = BeautifulSoup(response.content, features="html.parser")
    confirmation = f"Profile for { full_name } deleted"

    assert confirmation in soup.find(class_="govuk-notification-banner__heading").text


def test_own_profile_delete_view(state):
    perm = Permission.objects.get(codename="delete_person")
    state.user.user_permissions.add(perm)

    view_url = reverse(
        "profile-delete",
        kwargs={
            "profile_slug": state.person.slug,
        },
    )

    # CannotDeleteOwnProfileError is raised when user attempts to delete own profile
    with pytest.raises(CannotDeleteOwnProfileError):
        response = state.client.post(view_url)


def test_delete_view_with_other_users_profile(state):
    other_user = UserFactory(
        first_name="Other",
        last_name="User",
        email="other.user@test.com",  # /PS-IGNORE
        legacy_sso_user_id=None,
        username="other.user@-1111111@id.test.gov.uk",  # /PS-IGNORE
        sso_contact_email="other.user@test.com",  # /PS-IGNORE
    )
    other_user.save()
    other_person = PersonService().create_user_profile(other_user)

    assert Person.active.filter(pk=other_person.pk).exists()

    view_url = reverse(
        "profile-delete",
        kwargs={
            "profile_slug": other_person.slug,
        },
    )
    response = state.client.post(view_url, follow=True)
    next_url, status_code = response.redirect_chain[0]

    assert status_code == 302
    assert next_url == reverse("delete-confirmation")
    assert not Person.active.filter(pk=other_person.pk).exists()


def test_delete_profile_with_no_user(state):
    other_user = UserFactory(
        first_name="Other",
        last_name="User",
        email="other.user@example.com",  # /PS-IGNORE
        legacy_sso_user_id=None,
        username="other.user-11111111@example.com",  # /PS-IGNORE
        sso_contact_email="other.user@example.com",  # /PS-IGNORE
    )
    other_user.save()
    other_person = PersonService().create_user_profile(other_user)

    # remove the user from the profile
    other_person.user = None
    other_person.save()

    # try to delete the profile
    response = state.client.post(
        reverse("profile-delete", kwargs={"profile_slug": other_person.slug}),
        follow=True,
    )
    assertRedirects(response, reverse("delete-confirmation"), 302)
