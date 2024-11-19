from dataclasses import dataclass
from typing import Any, Optional

import pytest
from bs4 import BeautifulSoup
from django.contrib.auth.models import Group, Permission
from django.core.management import call_command
from django.db import models
from django.db.utils import IntegrityError
from django.test.client import Client
from django.urls import reverse
from pytest_django.asserts import assertContains

from networks.models import Network
from peoplefinder.forms.profile_edit import (
    AdminProfileEditForm,
    ContactProfileEditForm,
    LocationProfileEditForm,
    PersonalProfileEditForm,
    SkillsProfileEditForm,
    TeamsProfileEditForm,
    TeamsProfileEditFormset,
)
from peoplefinder.forms.role import RoleFormsetForm
from peoplefinder.management.commands.create_people_finder_groups import (
    PERSON_ADMIN_GROUP_NAME,
    TEAM_ADMIN_GROUP_NAME,
)
from peoplefinder.models import (
    AdditionalRole,
    Grade,
    KeySkill,
    LearningInterest,
    Person,
    Profession,
    Team,
    UkStaffLocation,
    Workday,
)
from peoplefinder.services.person import PersonService
from peoplefinder.test.factories import TeamFactory
from peoplefinder.types import EditSections
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


def test_edit_profile_personal(state):
    edit_profile_url = reverse(
        "profile-edit-section",
        kwargs={
            "profile_slug": state.person.slug,
            "edit_section": EditSections.PERSONAL.value,
        },
    )
    response = state.client.get(edit_profile_url)
    assert response.status_code == 200


def test_edit_profile_contact(state):
    edit_profile_url = reverse(
        "profile-edit-section",
        kwargs={
            "profile_slug": state.person.slug,
            "edit_section": EditSections.CONTACT.value,
        },
    )
    response = state.client.get(edit_profile_url)
    assert response.status_code == 200


def test_edit_profile_teams(state):
    edit_profile_url = reverse(
        "profile-edit-section",
        kwargs={
            "profile_slug": state.person.slug,
            "edit_section": EditSections.TEAMS.value,
        },
    )
    response = state.client.get(edit_profile_url)
    assert response.status_code == 200


def test_edit_profile_location(state):
    edit_profile_url = reverse(
        "profile-edit-section",
        kwargs={
            "profile_slug": state.person.slug,
            "edit_section": EditSections.LOCATION.value,
        },
    )
    response = state.client.get(edit_profile_url)
    assert response.status_code == 200


def test_edit_profile_skills(state):
    edit_profile_url = reverse(
        "profile-edit-section",
        kwargs={
            "profile_slug": state.person.slug,
            "edit_section": EditSections.SKILLS.value,
        },
    )
    response = state.client.get(edit_profile_url)
    assert response.status_code == 200


def test_edit_profile_admin_no_superuser(state):
    edit_profile_url = reverse(
        "profile-edit-section",
        kwargs={
            "profile_slug": state.person.slug,
            "edit_section": EditSections.ADMIN.value,
        },
    )
    response = state.client.get(edit_profile_url)
    assert response.status_code == 403


def test_edit_profile_admin_superuser(state):
    PersonService.update_groups_and_permissions(
        person=state.person,
        is_person_admin=False,
        is_team_admin=False,
        is_superuser=True,
    )

    edit_profile_url = reverse(
        "profile-edit-section",
        kwargs={
            "profile_slug": state.person.slug,
            "edit_section": EditSections.ADMIN.value,
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
    view_url = (
        reverse(
            "team-view",
            kwargs={
                "slug": state.team.slug,
            },
        )
        + "?sub_view=people"
    )
    check_visible_button(state, view_url, b"Edit team", "change_team")


def test_delete_team_visible_permission(state):
    view_url = (
        reverse(
            "team-view",
            kwargs={
                "slug": state.team.slug,
            },
        )
        + "?sub_view=people"
    )
    check_visible_button(state, view_url, b"Delete team", "delete_team")


def test_create_sub_team_visible_permission(state):
    view_url = (
        reverse(
            "team-view",
            kwargs={
                "slug": state.team.slug,
            },
        )
        + "?sub_view=people"
    )
    check_visible_button(state, view_url, b"Add new sub-team", "add_team")


def test_team_log_visible_permission(state):
    view_url = (
        reverse(
            "team-view",
            kwargs={
                "slug": state.team.slug,
            },
        )
        + "?sub_view=people"
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


def test_cannot_be_own_manager(state):
    assert state.person.manager is None
    state.person.save()

    state.person.manager = state.person
    with pytest.raises(IntegrityError):
        state.person.save()


def get_payload_value(value) -> Any:
    if obj_id := getattr(value, "id", None):
        value = obj_id
    elif isinstance(value, list) or isinstance(value, models.QuerySet):
        value = [get_payload_value(item) for item in value]
    return value


def payload_from_cleaned_data(form) -> dict:
    payload = {}

    for key, value in form.cleaned_data.items():
        if value:
            if form.prefix:
                payload[f"{form.prefix}-{key}"] = get_payload_value(value)
            else:
                payload[key] = get_payload_value(value)
    return payload


def test_profile_edit_personal_view(state):
    view_url = reverse(
        "profile-edit-section",
        kwargs={
            "profile_slug": state.person.slug,
            "edit_section": EditSections.PERSONAL.value,
        },
    )

    response = state.client.get(view_url)

    assert response.status_code == 200
    assert state.person.first_name is "Jane"
    assert state.person.last_name is "Smith"
    assert state.person.pronouns is None
    assert state.person.name_pronunciation is None

    form = PersonalProfileEditForm(
        {
            "preferred_first_name": "Jane",
            "last_name": "Smith",
            "pronouns": "she/her",
            "name_pronunciation": "Jay-n Smi-th",
        },
        instance=state.person,
    )
    assert form.is_valid()

    # Need to remove items with no value with cleaned data in order that "POST" will work
    payload = payload_from_cleaned_data(form)

    response = state.client.post(view_url, payload)

    assert response.status_code == 302
    assert response.url == view_url
    assert state.person.first_name == "Jane"
    assert state.person.last_name == "Smith"
    assert state.person.pronouns == "she/her"
    assert state.person.name_pronunciation == "Jay-n Smi-th"


def test_profile_edit_contact_view(state):
    view_url = reverse(
        "profile-edit-section",
        kwargs={
            "profile_slug": state.person.slug,
            "edit_section": EditSections.CONTACT.value,
        },
    )

    response = state.client.get(view_url)

    assert response.status_code == 200
    assert state.person.contact_email == "jane.smith@test.com"
    assert state.person.primary_phone_number is None
    assert state.person.secondary_phone_number is None

    form = ContactProfileEditForm(
        {
            "contact_email": "jane.smith123@test.com",
            "primary_phone_number": "01234567890",
            "secondary_phone_number": "09876543210",
        },
        instance=state.person,
    )
    assert form.is_valid()

    # Need to remove items with no value with cleaned data in order that "POST" will work
    payload = payload_from_cleaned_data(form)

    response = state.client.post(view_url, payload)

    assert response.status_code == 302
    assert response.url == view_url
    assert state.person.contact_email == "jane.smith123@test.com"
    assert state.person.primary_phone_number == "01234567890"
    assert state.person.secondary_phone_number == "09876543210"


def test_profile_edit_teams_view(state):
    view_url = reverse(
        "profile-edit-section",
        kwargs={
            "profile_slug": state.person.slug,
            "edit_section": EditSections.TEAMS.value,
        },
    )

    response = state.client.get(view_url)

    assert response.status_code == 200
    assert state.person.grade is None
    assert state.person.manager is None
    assert state.person.do_not_work_for_dit is False

    grade = Grade.objects.all().first()

    form = TeamsProfileEditForm(
        {
            "grade": grade,
            "do_not_work_for_dit": True,
        },
        instance=state.person,
    )
    form.is_valid()
    assert form.is_valid()

    # Need to remove items with no value with cleaned data in order that "POST" will work
    payload = {
        "teams-TOTAL_FORMS": "0",
        "teams-INITIAL_FORMS": "0",
    }
    payload.update(**payload_from_cleaned_data(form))

    response = state.client.post(view_url, payload)

    assert response.status_code == 302
    assert response.url == view_url
    assert state.person.grade == grade
    assert state.person.manager is None
    assert state.person.do_not_work_for_dit is True


def test_profile_edit_teams_formset_view(state):
    view_url = reverse(
        "profile-edit-section",
        kwargs={
            "profile_slug": state.person.slug,
            "edit_section": EditSections.TEAMS.value,
        },
    )

    response = state.client.get(view_url)

    assert response.status_code == 200
    assert state.person.roles.count() == 0

    form = TeamsProfileEditForm(
        {},
        instance=state.person,
    )
    assert form.is_valid()

    prefix = "teams-0"
    teams_formset_form = RoleFormsetForm(
        {
            f"{prefix}-person": state.person,
            f"{prefix}-team": state.team,
            f"{prefix}-job_title": "Job title",
            f"{prefix}-head_of_team": False,
            f"{prefix}-DELETE": False,
        },
        prefix="teams-0",
    )
    teams_formset_form.is_valid()
    assert teams_formset_form.is_valid()

    # Need to remove items with no value with cleaned data in order that "POST" will work
    payload = {
        "teams-TOTAL_FORMS": "1",
        "teams-INITIAL_FORMS": "0",
    }
    payload.update(**payload_from_cleaned_data(form))
    payload.update(**payload_from_cleaned_data(teams_formset_form))

    response = state.client.post(view_url, payload)

    assert response.status_code == 302
    assert response.url == view_url
    assert state.person.roles.count() == 1
    role = state.person.roles.first()
    assert role.person == state.person
    assert role.team == state.team
    assert role.job_title == "Job title"
    assert role.head_of_team is False


def test_profile_edit_location_view(state):
    view_url = reverse(
        "profile-edit-section",
        kwargs={
            "profile_slug": state.person.slug,
            "edit_section": EditSections.LOCATION.value,
        },
    )

    response = state.client.get(view_url)

    assert response.status_code == 200
    assert state.person.uk_office_location is None
    assert state.person.remote_working is None
    assert state.person.location_in_building is None
    assert state.person.international_building is None
    assert state.person.workdays.count() == 0

    uk_office_location = UkStaffLocation.objects.all().first()
    workday = Workday.objects.all().first()

    form = LocationProfileEditForm(
        {
            "uk_office_location": uk_office_location,
            "remote_working": Person.RemoteWorking.OFFICE_WORKER.value,
            "location_in_building": "3rd floor",
            "international_building": "international",
            "workdays": [workday],
        },
        instance=state.person,
    )
    assert form.is_valid()

    # Need to remove items with no value with cleaned data in order that "POST" will work
    payload = payload_from_cleaned_data(form)

    response = state.client.post(view_url, payload)

    assert response.status_code == 302
    assert response.url == view_url
    assert state.person.uk_office_location == uk_office_location
    assert state.person.remote_working == Person.RemoteWorking.OFFICE_WORKER
    assert state.person.location_in_building == "3rd floor"
    assert state.person.international_building == "international"
    assert state.person.workdays.count() == 1
    assert state.person.workdays.first() == workday


def test_profile_edit_skills_view(state):
    view_url = reverse(
        "profile-edit-section",
        kwargs={
            "profile_slug": state.person.slug,
            "edit_section": EditSections.SKILLS.value,
        },
    )

    response = state.client.get(view_url)

    assert response.status_code == 200
    assert state.person.key_skills.count() == 0
    assert state.person.other_key_skills is None
    assert state.person.fluent_languages is None
    assert state.person.intermediate_languages is None
    assert state.person.learning_interests.count() == 0
    assert state.person.other_learning_interests is None
    assert state.person.networks.count() == 0
    assert state.person.professions.count() == 0
    assert state.person.additional_roles.count() == 0
    assert state.person.other_additional_roles is None
    assert state.person.previous_experience is None

    key_skills = [KeySkill.objects.all().first()]
    learning_interests = [LearningInterest.objects.all().first()]
    networks = []
    # networks = [Network.objects.all().first()]
    professions = [Profession.objects.all().first()]
    additional_roles = [AdditionalRole.objects.all().first()]

    form = SkillsProfileEditForm(
        {
            "key_skills": key_skills,
            "other_key_skills": "Other key skills",
            "fluent_languages": "French",
            "intermediate_languages": "Italian",
            "learning_interests": learning_interests,
            "other_learning_interests": "Other learning interests",
            "networks": networks,
            "professions": professions,
            "additional_roles": additional_roles,
            "other_additional_roles": "Other additional roles",
            "previous_experience": "Previous experience",
        },
        instance=state.person,
    )
    assert form.is_valid()

    # Need to remove items with no value with cleaned data in order that "POST" will work
    payload = payload_from_cleaned_data(form)

    response = state.client.post(view_url, payload)

    assert response.status_code == 302
    assert response.url == view_url
    assert state.person.key_skills.count() == 1
    assert state.person.other_key_skills == "Other key skills"
    assert state.person.fluent_languages == "French"
    assert state.person.intermediate_languages == "Italian"
    assert state.person.learning_interests.count() == 1
    assert state.person.other_learning_interests == "Other learning interests"
    assert state.person.networks.count() == 0
    # assert state.person.networks.count() == 1
    assert state.person.professions.count() == 1
    assert state.person.additional_roles.count() == 1
    assert state.person.other_additional_roles == "Other additional roles"
    assert state.person.previous_experience == "Previous experience"


def test_profile_edit_admin_view(state):
    PersonService.update_groups_and_permissions(
        person=state.person,
        is_person_admin=False,
        is_team_admin=False,
        is_superuser=True,
    )

    view_url = reverse(
        "profile-edit-section",
        kwargs={
            "profile_slug": state.person.slug,
            "edit_section": EditSections.ADMIN.value,
        },
    )

    response = state.client.get(view_url)

    assert response.status_code == 200
    assert state.person.user.is_superuser == True
    assert (
        state.person.user.groups.filter(name=PERSON_ADMIN_GROUP_NAME).exists() == False
    )
    assert state.person.user.groups.filter(name=TEAM_ADMIN_GROUP_NAME).exists() == False

    form = AdminProfileEditForm(
        {
            "is_person_admin": True,
            "is_team_admin": True,
            "is_superuser": False,
        },
        instance=state.person,
        request_user=state.user,
    )
    assert form.is_valid()

    # Need to remove items with no value with cleaned data in order that "POST" will work
    payload = payload_from_cleaned_data(form)

    response = state.client.post(view_url, payload)

    assert response.status_code == 302
    assert response.url == view_url

    state.person.user.refresh_from_db()
    assert state.person.user.groups.filter(name=PERSON_ADMIN_GROUP_NAME).exists()
    assert state.person.user.groups.filter(name=TEAM_ADMIN_GROUP_NAME).exists()
    assert state.person.user.is_superuser == False


def test_user_admin_no_superuser(state):
    PersonService.update_groups_and_permissions(
        person=state.person,
        is_person_admin=False,
        is_team_admin=False,
        is_superuser=False,
    )
    view_url = reverse(
        "profile-edit-section",
        kwargs={
            "profile_slug": state.person.slug,
            "edit_section": EditSections.PERSONAL.value,
        },
    )

    response = state.client.get(view_url)

    assert response.status_code == 200

    soup = BeautifulSoup(response.content, features="html.parser")

    assert not soup.find(
        lambda tag: tag.name == "a" and "Administer profile" in tag.text
    )


def test_user_admin_with_superuser(state):
    PersonService.update_groups_and_permissions(
        person=state.person,
        is_person_admin=False,
        is_team_admin=False,
        is_superuser=True,
    )
    view_url = reverse(
        "profile-edit-section",
        kwargs={
            "profile_slug": state.person.slug,
            "edit_section": EditSections.PERSONAL.value,
        },
    )

    response = state.client.get(view_url)

    assert response.status_code == 200

    soup = BeautifulSoup(response.content, features="html.parser")

    assert soup.find(lambda tag: tag.name == "a" and "Administer profile" in tag.text)


def test_user_admin_no_superuser_but_team_person_admin(state):
    PersonService.update_groups_and_permissions(
        person=state.person,
        is_person_admin=True,
        is_team_admin=True,
        is_superuser=False,
    )
    view_url = reverse(
        "profile-edit-section",
        kwargs={
            "profile_slug": state.person.slug,
            "edit_section": EditSections.PERSONAL.value,
        },
    )

    response = state.client.get(view_url)

    assert response.status_code == 200

    soup = BeautifulSoup(response.content, features="html.parser")

    assert not soup.find(
        lambda tag: tag.name == "a" and "Administer profile" in tag.text
    )


class TestProfileUpdateUserView:
    def _update_user(self, client, profile, new_user):
        return client.post(
            reverse("profile-update-user", kwargs={"profile_slug": profile.slug}),
            {"username": new_user.username},
        )

    def test_swap_user(self, normal_user, state):
        PersonService.update_groups_and_permissions(
            person=state.person,
            is_person_admin=False,
            is_team_admin=False,
            is_superuser=True,
        )

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
