from django.core.management.base import BaseCommand
from peoplefinder.ingest import UkOfficeLocationsS3Ingest


class Command(BaseCommand):
    help = "Ingest the UK Staff Locations"

    def handle(self, *args, **options):
        UkOfficeLocationsS3Ingest()

        self.stdout.write(
            self.style.SUCCESS("Successfully ingested UK Office Locations\n")
        )
