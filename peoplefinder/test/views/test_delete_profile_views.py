import pytest

from bs4 import BeautifulSoup

from dataclasses import dataclass
from django.contrib.auth.models import (
    Permission,
)
from django.test.client import Client
from django.urls import reverse

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
    user.is_using_peoplefinder_v2 = True
    user.save()
    person = PersonService().create_user_profile(user)
    client = Client()
    client.force_login(user)
    return State(client=client, person=person, team=team, user=user)


def button_is_visible(content, id) -> bool:
    soup = BeautifulSoup(content, features="html.parser")

    # Find delete 'button'
    return bool(soup.find("input", {"id": id}))


def test_user_cannot_view_own_profile_delete_button_with_permission(state):
    profile_url = reverse(
        "profile-view",
        kwargs={
            "profile_slug": state.person.slug,
        },
    )

    delete_profile_perm = Permission.objects.get(codename="delete_profile")
    state.user.user_permissions.add(delete_profile_perm)

    response = state.client.get(profile_url)
    assert response.status_code == 200

    assert not button_is_visible(response.content, "delete-profile")


def test_profile_delete_button_visible_with_permission(state):
    other_user = UserFactory(
        first_name="Fred",
        last_name="Carter",
        email="fred.carter@test.com",
        legacy_sso_user_id=None,
        username="fred.carter@-1111111@id.test.gov.uk",
        sso_contact_email="fred.carter@test.com",
        is_using_peoplefinder_v2=True,
    )
    other_user.save()
    other_person = PersonService().create_user_profile(other_user)

    profile_url = reverse(
        "profile-view",
        kwargs={
            "profile_slug": other_person.slug,
        },
    )

    delete_profile_perm = Permission.objects.get(codename="delete_profile")
    state.user.user_permissions.add(delete_profile_perm)

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

    # Test with session variable gives 200 response - no redirection
    session = state.client.session
    session["profile_name"] = state.person.full_name
    session.save()

    response = state.client.get(view_url)

    assert response.status_code == 200

    # Check confirmation message
    full_name = session["profile_name"]
    soup = BeautifulSoup(response.content, features="html.parser")
    confirmation = f"Profile for { full_name } deleted"

    assert bool(
        confirmation in soup.find(class_="govuk-notification-banner__heading").text
    )


def test_own_profile_delete_view(state):
    perm = Permission.objects.get(codename="delete_profile")
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


def test_other_user_profile_delete_view(state):
    other_user = UserFactory(
        first_name="Victor",
        last_name="McDaid",
        email="victor.mcdaid@test.com",
        legacy_sso_user_id=None,
        username="victor.macdaid@-1111111@id.test.gov.uk",
        sso_contact_email="victor.mcdaid@test.com",
        is_using_peoplefinder_v2=True,
    )
    other_user.save()
    other_person = PersonService().create_user_profile(other_user)

    assert Person.objects.filter(pk=other_person.pk).exists()

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
    assert not Person.objects.filter(pk=other_person.pk).exists()
