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
            first_name="Fred",
            last_name="Carter",
            email="fred.carter@test.com",
            legacy_sso_user_id=None,
            username="fred.carter@-1111111@id.test.gov.uk",
            sso_contact_email="fred.carter@test.com",
        )

        user_victor = UserFactory(
            first_name="Victor",
            last_name="McDaid",
            email="victor.mcdaid@test.com",
            legacy_sso_user_id=None,
            username="victor.macdaid@-1111111@id.test.gov.uk",
            sso_contact_email="victor.mcdaid@test.com",
            is_staff=False,
            is_superuser=False,
            is_using_peoplefinder_v2=True,
        )

        self.stdout.write(self.style.SUCCESS("Job completed successfully"))
