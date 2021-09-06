from django.core.management.base import BaseCommand

from peoplefinder.services.person import PersonService
from user.models import User


class Command(BaseCommand):
    help = "Create user profiles for local testing purposes"

    def handle(self, *args, **options):
        self.created = 0

        person_service = PersonService()
        users_without_profile = User.objects.filter(profile=None)

        for user in users_without_profile:
            profile = person_service.create_user_profile(user)
            self.stdout.write(f"Profile created for {profile.full_name}")
            self.created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Job completed successfully\n{self.created} profiles created"
            )
        )
