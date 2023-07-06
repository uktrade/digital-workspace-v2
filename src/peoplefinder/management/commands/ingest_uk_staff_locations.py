from django.core.management.base import BaseCommand
from django.db import connections

from peoplefinder.models import UkStaffLocation


class Command(BaseCommand):
    help = "Ingest the UK Staff Locations"

    def handle(self, *args, **options):
        existing_uk_staff_locations = list(
            UkStaffLocation.objects.all().values_list("pk", flat=True)
        )

        updated = 0
        created = 0
        deleted = 0

        with connections["uk_staff_locations"].cursor() as cursor:
            cursor.execute(
                """
                SELECT location_code, location_name, city
                FROM dit.uk_staff_locations
                """
            )
            for row in cursor.fetchall():
                location_code = row[0]
                location_name = row[1]
                city = row[2]
                (
                    uk_staff_location,
                    location_created,
                ) = UkStaffLocation.objects.update_or_create(
                    code=location_code,
                    defaults={
                        "is_active": True,
                        "name": location_name,
                        "city": city,
                    },
                )

                if location_created:
                    created += 1
                else:
                    updated += 1

                if uk_staff_location.pk in existing_uk_staff_locations:
                    existing_uk_staff_locations.remove(uk_staff_location.pk)

        if existing_uk_staff_locations:
            deleted = UkStaffLocation.objects.filter(
                pk__in=existing_uk_staff_locations
            ).update(is_active=False)

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully ingested UK Staff Locations\n"
                f"Created: {created}\n"
                f"Updated: {updated}\n"
                f"Deleted: {deleted}\n"
            )
        )
