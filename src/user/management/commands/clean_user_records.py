from typing import List, Tuple

from django.core.management.base import BaseCommand
from django.db.models import Count

from user.models import User
from peoplefinder.models import Person


class Command(BaseCommand):
    help = "Clean up and archive User and Person records"

    def add_arguments(self, parser):
        parser.add_argument("days", type=int)

    def handle(self, *args, **options):
        days = options["days"]
        self.deleted_users = 0
        self.deleted_profiles = 0
        self.archived = 0

        self.delete_users_and_profiles()
        self.archive_users(login_older_than=days)

        self.stdout.write(
            self.style.SUCCESS(
                "Job finished successfully\n"
                f"{self.deleted_users} User records deleted\n"
                f"{self.deleted_profiles} Person records deleted\n"
                f"{self.archived} User and Person records with logins older than {days} days have been archived\n"
            )
        )

    def delete_users_and_profiles(self):
        
        self.created += 1


    def archive_users(self, login_older_than=90):
        ...






all_users = User.objects.values_list('email', flat=True)
all_users_d = all_users.distinct()
all_users_np = all_users.filter(profile__isnull=True)
all_valid_users = User.objects.filter(profile__isnull=False)

all_pf = Person.objects.all()
all_pf_nu = all_pf.filter(user__isnull=True)
inactive_profiles = all_valid_users.filter(profile__is_active=False)

duplicate_emails = User.objects.values('email').annotate(email_count=Count('email')).filter(email_count__gt=1)


len(all_users)
14935
len(all_users_d)
13540
len(all_users_np)
3231
len(all_valid_users)
11704

len(all_pf)
12128
len(inactive_profiles)
1952

all_valid_users.filter(is_active=True).count()
11702
all_valid_users.filter(profile__is_active=True).count()
9752
all_valid_users.filter(email__in=list(duplicate_emails))
<QuerySet []>


all_valid_users.filter(profile__is_active=True).order_by("last_login").values_list("last_login")
<QuerySet [(datetime.datetime(2021, 3, 3, 22, 53, 12, 638694, tzinfo=datetime.timezone.utc),), (datetime.datetime(2021, 3, 4, 9, 52, 24, 452110, tzinfo=datetime.timezone.utc),), (datetime.datetime(2021, 3, 4, 9, 54, 26, 34597, tzinfo=datetime.timezone.utc),), (datetime.datetime(2021, 3, 4, 10, 25, 17, 354960, tzinfo=datetime.timezone.utc),), (datetime.datetime(2021, 3, 5, 15, 2, 12, 318794, tzinfo=datetime.timezone.utc),), (datetime.datetime(2021, 3, 5, 15, 39, 9, 553546, tzinfo=datetime.timezone.utc),), (datetime.datetime(2021, 3, 10, 1, 55, 0, 220466, tzinfo=datetime.timezone.utc),), (datetime.datetime(2021, 3, 10, 8, 48, 19, 575364, tzinfo=datetime.timezone.utc),), (datetime.datetime(2021, 3, 10, 14, 22, 12, 235418, tzinfo=datetime.timezone.utc),), (datetime.datetime(2021, 3, 11, 12, 38, 59, 750584, tzinfo=datetime.timezone.utc),), (datetime.datetime(2021, 3, 12, 10, 43, 27, 901595, tzinfo=datetime.timezone.utc),), (datetime.datetime(2021, 3, 12, 12, 43, 13, 964399, tzinfo=datetime.timezone.utc),), (datetime.datetime(2021, 3, 12, 15, 22, 4, 872245, tzinfo=datetime.timezone.utc),), (datetime.datetime(2021, 3, 13, 9, 7, 47, 607027, tzinfo=datetime.timezone.utc),), (datetime
