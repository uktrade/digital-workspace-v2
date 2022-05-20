from django.core.management.base import BaseCommand

from user.test.factories import UserFactory


class Command(BaseCommand):
    help = """Create user profiles for local testing purposes"""

    def handle(self, *args, **options):
        test_user = UserFactory(
            first_name="Test",
            last_name="User",
            email="test.user@test.com",  # /PS-IGNORE
            legacy_sso_user_id=None,
            username="test.user@-1111111@id.test.gov.uk",  # /PS-IGNORE
            sso_contact_email="test.user@test.com",  # /PS-IGNORE
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"{test_user.first_name} {test_user.last_name} ({test_user.email}) was created"
            )
        )

        another_user = UserFactory(
            first_name="Another",
            last_name="User",
            email="another.user@test.com",  # /PS-IGNORE
            legacy_sso_user_id=None,
            username="another.user@-1111111@id.test.gov.uk",  # /PS-IGNORE
            sso_contact_email="another.user@test.com",  # /PS-IGNORE
            is_staff=False,
            is_superuser=False,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"{another_user.first_name} {another_user.last_name} ({another_user.email}) was created"
            )
        )
