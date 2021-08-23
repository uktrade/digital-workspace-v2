from dataclasses import dataclass
from typing import List

import pytest
from django.test.client import Client

from peoplefinder.models import Person, Team
from peoplefinder.test.factories import TeamFactory
from user.models import User
from user.test.factories import UserFactory


@dataclass
class State:
    client: Client
    paths: List[str]
    user: User


@pytest.fixture
def state(db):
    team = TeamFactory()
    user = UserFactory()
    Person.objects.create(user=user)

    client = Client()
    client.force_login(user)

    paths = [
        f"/people/{user.id}/",
        f"/teams/{team.slug}/",
    ]

    return State(client=client, paths=paths, user=user)


def test_redirect_to_v1(state, settings):
    settings.PEOPLEFINDER_V2 = False

    for path in state.paths:
        response = state.client.get(path)

        assert response.status_code == 302
        assert response.url == settings.PEOPLEFINDER_URL + path


def test_redirect_to_v1_when_user_not_enabled(state, settings):
    settings.PEOPLEFINDER_V2 = True

    for path in state.paths:
        response = state.client.get(path)

        assert response.status_code == 302
        assert response.url == settings.PEOPLEFINDER_URL + path


def test_allow_to_v2(state, settings):
    settings.PEOPLEFINDER_V2 = True

    state.user.is_using_peoplefinder_v2 = True
    state.user.save()

    for path in state.paths:
        response = state.client.get(path)

        assert response.status_code == 200
