from django.core.management.base import BaseCommand
from django.core.management import call_command

from peoplefinder.models import Person
from peoplefinder.services.person import PersonService

from user.test.factories import UserFactory


class Command(BaseCommand):
    help = """Create user profiles for local testing purposes"""

    def handle(self, *args, **options):
        person_service = PersonService()

        # create users
        user_jane = UserFactory()

        user_fred = UserFactory(
            first_name = "Fred",
            last_name = "Carter",
            email = "fred.carter@test.com",
            legacy_sso_user_id = None,
            username = "fred.carter@-1111111@id.test.gov.uk",
            sso_contact_email = "fred.carter@test.com",
        )

        user_victor = UserFactory(
            first_name = "Victor",
            last_name = "McDaid",
            email = "victor.mcdaid@test.com",
            legacy_sso_user_id = None,
            username = "victor.macdaid@-1111111@id.test.gov.uk",
            sso_contact_email = "victor.mcdaid@test.com",
            is_staff=False,
            is_superuser=False,
            is_using_peoplefinder_v2=True,
        )
        

        # TODO: Do I need the following if statement (from conftext.py)??? If so, then you will need one for each of the users above.
        # TODO: If not required, then you probably won't need the variabe names above either - you can create users without assigning them to (named) variables.
        if hasattr(user_jane, "profile"):
            # We need to delete the profile's audit log separately because the primary
            # key is always the same when using a one-to-one relationship.
            AuditLogService.get_audit_log(user_jane.profile).delete()
            user_jane.profile.delete()

        # TODO: Check with Ross, but I don't think I need to call_command in this file. Therefore the next couple of executable lines don't need to be here.
        # teams
        call_command("create_test_teams")

        # profiles
        call_command("create_user_profiles")

        self.stdout.write(self.style.SUCCESS("Job completed successfully"))