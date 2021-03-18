from django.core.management.base import BaseCommand

from peoplefinder.models import Person
from user.models import User


class Command(BaseCommand):
    help = "Create user profiles for local testing purposes"

    def handle(self, *args, **options):
        self.created = 0

        users_without_profile = User.objects.filter(profile=None)

        for user in users_without_profile:
            Person.objects.create(user=user)
            self.stdout.write(f"Profile created for {user.get_full_name()}")
            self.created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Job completed successfully\n{self.created} profiles created"
            )
        )
