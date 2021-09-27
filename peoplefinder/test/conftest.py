import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from peoplefinder.models import Team
from peoplefinder.services.audit_log import AuditLogService
from peoplefinder.services.person import PersonService


@pytest.fixture(scope="package")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        User = get_user_model()

        # John Smith - normal user
        user_john_smith, _ = User.objects.get_or_create(
            username="johnsmith",
            first_name="John",
            last_name="Smith",
            email="john.smith@example.com",
            legacy_sso_user_id="john-smith-sso-user-id",
            is_staff=False,
            is_superuser=False,
            is_using_peoplefinder_v2=True,
        )

        if hasattr(user_john_smith, "profile"):
            # We need to delete the profile's audit log separately because the primary
            # key is always the same when using a one-to-one relationship.
            AuditLogService.get_audit_log(user_john_smith.profile).delete()
            user_john_smith.profile.delete()

        call_command("create_test_teams")
        call_command("create_user_profiles")
        call_command("create_people_finder_groups")

        user_john_smith.refresh_from_db()

        team_software = Team.objects.get(slug="software")

        user_john_smith.profile.roles.get_or_create(
            team=team_software,
            job_title="Software Engineer",
        )

        PersonService().profile_updated(None, user_john_smith.profile, user_john_smith)

        # Leave this here to check we have reset the db into a known state.
        assert AuditLogService.get_audit_log(user_john_smith.profile).count() == 2
