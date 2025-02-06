from datetime import timedelta
import requests
from urllib.parse import urlparse, urlunparse

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from user.models import User
from peoplefinder.models import Person


class Command(BaseCommand):
    help = "Clean up and archive User and Person records"

    def add_arguments(self, parser):
        parser.add_argument("days", type=int, default=90)
        parser.add_argument("limit", type=int, default=25)
        parser.add_argument("offset", type=int, default=0)

    def handle(self, *args, **options):
        days = options["days"]
        limit = options["limit"]
        offset = options["offset"]

        self.sync_inactive_users_profiles()

        login_cutoff_date = timezone.now() - timedelta(days=days)
        users_to_check = User.objects.filter(is_active=True).filter(
            last_login__lt=login_cutoff_date
        )
        number_of_users = users_to_check.count()

        if limit == 0:
            batch = users_to_check
            self.stdout.write(
                self.style.NOTICE(
                    f"Checking all {number_of_users} User records with last_login older than {days} ago"
                )
            )
        else:
            batch = users_to_check[offset:limit]
            self.stdout.write(
                self.style.NOTICE(
                    f"Checking {limit} (from record {offset}) of {number_of_users} User records with last_login older than {days} ago"
                )
            )

        deactivated = 0
        ignored = 0
        # check against SSO API endpoint to see if user is active there
        authbroker_url = urlparse(settings.AUTHBROKER_URL)
        url = urlunparse(authbroker_url._replace(path="/introspect/"))
        headers = {"Authorization": f"bearer {settings.AUTHBROKER_INTROSPECTION_TOKEN}"}

        for user in batch:
            params = {"email": user.email}
            response = requests.get(url, params, headers=headers, timeout=5)
            if response.status_code == 200:
                resp_json = response.json()
                if not resp_json["is_active"]:
                    user.is_active = False
                    user.save()
                    deactivated += 1
                else:
                    ignored += 1
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"SSO introspect endpoint returned {response.status_code} status code for {user.email}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                "Job finished successfully\n"
                f"{deactivated} User records marked as inactive\n"
                f"{ignored} User records left as active\n"
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
