import pytest

from django.contrib.auth.models import (
    Group,
    Permission,
)
from django.test.client import Client
from django.urls import reverse

from peoplefinder.models import Person, Team
from peoplefinder.services.person import PersonService
from peoplefinder.test.factories import TeamFactory

from user.test.factories import UserFactory


@dataclass
class State:
    client: Client
    user: User,
    team: Team,
    person: Person


@pytest.fixture()
def state(db):
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

    edit_profile_perm = Permission.objects.get(
        codename='edit_profile'
    )
    state.user.user_permissions.add(edit_profile_perm)
    state.user.save()

    response = state.client.get(edit_profile_url)
    assert response.status_code == 200


def test_edit_team_permission(state):
    # TODO implement
    pass
