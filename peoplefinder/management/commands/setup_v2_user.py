from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand, CommandError

from user.models import User


class Command(BaseCommand):
    help = """Create user profiles for local testing purposes"""

    def add_arguments(self, parser):
        parser.add_argument("email", type=str)

    def handle(self, *args, **options):
        email = options["email"]
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise CommandError('User with email "%s" does not exist' % email)

        user.is_using_peoplefinder_v2 = True
        user.user_permissions.add(Permission.objects.get(codename="delete_profile"))
        user.user_permissions.add(Permission.objects.get(codename="edit_profile"))
        user.save()

        self.stdout.write(
            self.style.SUCCESS("User profile set to use PF v2 successfully")
        )
