from django.core.management.base import BaseCommand
from src.peoplefinder.ingest import DBTSectorsS3Ingest


class Command(BaseCommand):
    help = "Ingest the DBT Sectors"

    def handle(self, *args, **options):
        DBTSectorsS3Ingest()

        self.stdout.write(self.style.SUCCESS("Successfully ingested DBT Sectors\n"))
