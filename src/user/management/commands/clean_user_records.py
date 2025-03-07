from django.core.management.base import BaseCommand
from django.db.models import Count

from user.models import User
from peoplefinder.models import Person


class Command(BaseCommand):
    help = "Clean up User and Person records"

    def handle(self, *args, **options):
        users_without_profile = User.objects.filter(profile__isnull=True)
        self.do_delete(users_without_profile, "User")

        profiles_without_user = Person.objects.filter(user__isnull=True)
        self.do_delete(profiles_without_user, "Person")

        no_duplicate_emails = (
            User.objects.values("email")
            .annotate(email_count=Count("email"))
            .filter(email_count__gt=1)
            .count()
        )
        if no_duplicate_emails > 0:
            self.stdout.write(
                self.style.NOTICE(
                    f"Found {no_duplicate_emails} User records with duplicate emails"
                )
            )

    def do_delete(self, queryset, model_name):
        self.stdout.write(
            self.style.NOTICE(
                f"Found {queryset.count()} {model_name} records with no associated Person profile"
            )
        )
        try:
            queryset.delete()
            self.stdout.write(
                self.style.SUCCESS("Batch {model_name} deletion successful")
            )
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f"Batch {model_name} deletion stopped with error: {e}")
            )
            count = 0
            for record in queryset:
                try:
                    record.delete()
                    count += 1
                except Exception as e:
                    self.stderr.write(
                        self.style.ERROR(
                            f"{model_name} {record} deletion raised error: {e}"
                        )
                    )
            self.stdout.write(
                self.style.SUCCESS(
                    "One-by-one deletion successful for {count} {model_name} records"
                )
            )
