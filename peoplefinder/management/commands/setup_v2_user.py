from django.core.management.base import BaseCommand, CommandError

from peoplefinder.models import Person
from peoplefinder.services.person import PersonService
from user.models import User


class Command(BaseCommand):
    help = """Set chosen user profile to use People Findder v2 for local testing purposes"""

    def add_arguments(self, parser):
        parser.add_argument("email", type=str)

    def handle(self, *args, **options):
        email = options["email"]
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise CommandError(f"User with email {email} does not exist")

        user.is_using_peoplefinder_v2 = True
        user.save()

        person, _ = Person.objects.get_or_create(user=user)

        PersonService.update_groups_and_permissions(
            person=person,
            is_person_admin=True,
            is_team_admin=True,
            is_superuser=True,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"User profile for {user.first_name} {user.last_name} ({user.email}) set to use PF v2 successfully"
            )
        )
