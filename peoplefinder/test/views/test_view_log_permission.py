# govuk-details__summary-text

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

from peoplefinder.test.views.test_profile_views import state

def test_team_log_visible_permission(state):
    view_url = reverse(
        "team-view",
        kwargs={
            'slug': state.team.slug,
        }
    )
    response = state.client.get(view_url)
    assert response.status_code == 200
    title = b"Audit log"
    assert title not in response.content
    soup = BeautifulSoup(response.content, features="html.parser")

    log_detail = soup.find_all(attrs={"data-module": "govuk-details"})
    log_detail_len = len(log_detail)

    view_log_perm = Permission.objects.get(
        codename="view_auditlog_team"
    )
    state.user.user_permissions.add(view_log_perm)

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
            'profile_slug': state.person.slug,
        }
    )
    response = state.client.get(view_url)
    assert response.status_code == 200
    title = b"Audit log"
    assert title in response.content


def test_profile_log_visible_permission(state):
    other_user = UserFactory(
        username="aa",
        legacy_sso_user_id = "aa"
    )
    other_user.is_using_peoplefinder_v2 = True
    other_user.save()
    other_person = PersonService().create_user_profile(other_user)

    view_url = reverse(
        "profile-view",
        kwargs={
            'profile_slug': other_person.slug,
        }
    )
    response = state.client.get(view_url)
    assert response.status_code == 200
    title = b"Audit log"
    assert title not in response.content
    soup = BeautifulSoup(response.content, features="html.parser")

    log_detail = soup.find_all(attrs={"data-module": "govuk-details"})
    log_detail_len = len(log_detail)

    view_log_perm = Permission.objects.get(
        codename="view_auditlog"
    )
    state.user.user_permissions.add(view_log_perm)

    response = state.client.get(view_url)
    assert response.status_code == 200
    assert title in response.content
    soup = BeautifulSoup(response.content, features="html.parser")
    log_detail = soup.find_all(attrs={"data-module": "govuk-details"})
    assert len(log_detail) == log_detail_len + 1
