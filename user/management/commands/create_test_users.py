from typing import List, Tuple

from django.core.management.base import BaseCommand

from user.models import User

# first name, last name
USERS: List[Tuple[str, str]] = [
    ("John", "Smith"),
    ("Jane", "Doe"),
    ("Elon", "Musk"),
    ("Bill", "Gates"),
    ("Ada", "Lovelace"),
    ("Grace", "Hopper"),
]


class Command(BaseCommand):
    help = "Create users for local testing purposes"

    def handle(self, *args, **options):
        self.exists = 0
        self.created = 0

        for first_name, last_name in USERS:
            self.create_user(first_name, last_name)

        self.stdout.write(
            self.style.SUCCESS(
                "Job finished successfully\n"
                f"{self.exists} users already existed\n"
                f"{self.created} users created"
            )
        )

    def create_user(self, first_name: str, last_name: str) -> User:
        username = f"{first_name.lower()}.{last_name.lower()}@example.com"

        try:
            user = User.objects.get(username=username)
            self.stdout.write(f"{username} already exists")
            self.exists += 1
        except User.DoesNotExist:
            user = User.objects.create_user(
                username,
                email=username,
                first_name=first_name,
                last_name=last_name,
            )
            self.stdout.write(f"{username} created")
            self.created += 1

        return user
