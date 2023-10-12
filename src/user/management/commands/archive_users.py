from django.core.management.base import BaseCommand
from django.utils import timezone

from user.models import User
from peoplefinder.models import Person


class Command(BaseCommand):
    help = "Clean up and archive User and Person records"

    def add_arguments(self, parser):
        parser.add_argument("days", type=int, default=90)
        parser.add_argument("batch_size", type=int, default=25)
        parser.add_argument("batch_start", type=int, default=0)

    def handle(self, *args, **options):
        days = options["days"]
        batch_size = options["batch_size"]
        batch_start = options["batch_start"]

        self.sync_inactive_users_profiles()

        login_cutoff_date = timezone.now() - timedelta(days=days)
        users_to_check = User.objects.filter(is_active=True).filter(
            last_login__lt=login_cutoff_date
        )
        number_of_users = users_to_check.count()

        if batch_size == 0:
            batch = users_to_check
            self.stdout.write(
                self.style.NOTICE(
                    f"Checking all {number_of_users} User records with last_login older than {days} ago"
                )
            )
        else:
            batch = users_to_check[batch_start:batch_size]
            self.stdout.write(
                self.style.NOTICE(
                    f"Checking {batch_size} (from record {batch_start}) of {number_of_users} User records with last_login older than {days} ago"
                )
            )

        deactivated = 0
        ignored = 0
        for user in batch:
            # check against SSO API endpoint to see if user is active there
            # if sso record is inactive:
            # user.is_active = False
            # user.save()
            # deactivated += 1
            # else:
            # ignored += 1
            ...

        self.stdout.write(
            self.style.SUCCESS(
                "Job finished successfully\n"
                f"{self.deactivated} User records marked as inactive\n"
                f"{self.ignored} User records left as active\n"
            )
        )

    def sync_inactive_users_profiles(self):
        mismatched_users = User.objects.filter(profile__is_active=False).filter(
            is_active=True
        )
        mismatched_users.update(active=False)
        self.stdout.write(
            self.style.SUCCESS(
                f"Updated {mismatched_users.count()} active User records with inactive Person profiles to inactive"
            )
        )

        mismatched_profiles = Person.objects.filter(is_active=True).filter(
            user__is_active=False
        )
        mismatched_profiles.update(active=False)
        self.stdout.write(
            self.style.SUCCESS(
                f"Updated {mismatched_profiles.count()} active Person records with inactive User records to inactive"
            )
        )
