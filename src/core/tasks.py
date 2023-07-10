from config.celery import celery_app
from peoplefinder.services.uk_staff_locations import UkStaffLocationService


@celery_app.task(bind=True)
def debug_task(self):
    print("Request: {0!r}".format(self.request))  # noqa


@celery_app.task(bind=True)
def ingest_uk_staff_locations(self):
    ingest_output = UkStaffLocationService().ingest_uk_staff_locations()

    created = ingest_output["created"]
    updated = ingest_output["updated"]
    deleted = ingest_output["deleted"]

    print(
        f"Successfully ingested UK Staff Locations\n"
        f"Created: {created}\n"
        f"Updated: {updated}\n"
        f"Deleted: {deleted}\n"
    )
