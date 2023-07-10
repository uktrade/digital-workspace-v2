from django.core.management.base import BaseCommand
from django.db import connections

from peoplefinder.models import UkStaffLocation
from peoplefinder.services.uk_staff_locations import UkStaffLocationService


class Command(BaseCommand):
    help = "Ingest the UK Staff Locations"

    def handle(self, *args, **options):
        ingest_output = UkStaffLocationService().ingest_uk_staff_locations()

        created = ingest_output["created"]
        updated = ingest_output["updated"]
        deleted = ingest_output["deleted"]

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully ingested UK Staff Locations\n"
                f"Created: {created}\n"
                f"Updated: {updated}\n"
                f"Deleted: {deleted}\n"
            )
        )
