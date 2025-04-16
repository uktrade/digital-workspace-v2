from django.core.management import call_command

from config.celery import celery_app
from core.utils import cache_lock
from feedback import utils
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


@celery_app.task(bind=True)
@cache_lock(cache_key="update_search_index")
def update_search_index(self):
    # Run update_index
    call_command("update_index")


@celery_app.task(bind=True)
def schedule_feedback_email_notification(self):
    feedback_received = utils.feedback_received_within()
    if not feedback_received:
        return
    utils.send_feedback_notification()
