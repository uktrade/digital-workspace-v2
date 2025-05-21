import pytest
from django.contrib.auth.models import Group
from django.core.management import call_command

from peoplefinder.management.commands.create_people_finder_groups import (
    TEAM_ADMIN_GROUP_NAME,
)
from peoplefinder.models import Team
from peoplefinder.services.audit_log import AuditLogService
from peoplefinder.services.person import PersonService
from user.models import User


@pytest.fixture(scope="package")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        # John Smith - normal user
        user_john_smith, _ = User.objects.get_or_create(
            username="johnsmith",
            first_name="John",
            last_name="Smith",
            email="john.smith@example.com",
            legacy_sso_user_id="john-smith-sso-user-id",
            is_staff=False,
            is_superuser=False,
        )

        if hasattr(user_john_smith, "profile"):
            # We need to delete the profile's audit log separately because the primary
            # key is always the same when using a one-to-one relationship.
            AuditLogService.get_audit_log(user_john_smith.profile).delete()
            user_john_smith.profile.delete()

        call_command("loaddata", "countries.json")
        call_command("loaddata", "uk_staff_locations.json")
        call_command("loaddata", "uk_office_locations.json")
        call_command("loaddata", "dbt_sectors.json")
        call_command("create_test_teams")
        call_command("create_user_profiles")
        call_command("create_people_finder_groups")
        call_command("create_section_homepages")

        user_john_smith.refresh_from_db()

        team_software = Team.objects.get(slug="software")

        user_john_smith.profile.preferred_first_name = "J"
        user_john_smith.profile.save(update_fields=["preferred_first_name"])

        user_john_smith.profile.roles.get_or_create(
            team=team_software,
            job_title="Software Engineer",
        )

        PersonService().profile_updated(None, user_john_smith.profile, user_john_smith)

        # Leave this here to check we have reset the db into a known state.
        assert AuditLogService.get_audit_log(user_john_smith.profile).count() == 2

        call_command("update_index")


@pytest.fixture
def normal_user(db):
    return User.objects.get(username="johnsmith")


@pytest.fixture
def another_normal_user(db, django_db_blocker):
    """
    Useful when you need a user that's not the one you're logged in as
    """
    with django_db_blocker.unblock():
        # Jane Smith - another normal user
        user_jane_smith, _ = User.objects.get_or_create(
            username="janesmith",
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@example.com",
            legacy_sso_user_id="jane-smith-sso-user-id",
            is_staff=False,
            is_superuser=False,
        )
        PersonService().create_user_profile(user_jane_smith)

        call_command("create_test_teams")
        team_spacex = Team.objects.get(slug="spacex")

        user_jane_smith.profile.roles.get_or_create(
            team=team_spacex,
            job_title="Software Engineer",
        )

        PersonService().profile_updated(None, user_jane_smith.profile, user_jane_smith)

        call_command("update_index")

        return user_jane_smith


@pytest.fixture
def team_admin_user(normal_user):
    normal_user.groups.add(Group.objects.get(name=TEAM_ADMIN_GROUP_NAME))
    normal_user.is_staff = True
    normal_user.save()

    return normal_user


@pytest.fixture
def software_team(db):
    return Team.objects.get(slug="software")
