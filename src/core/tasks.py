from django.core.cache import cache
from django.core.management import call_command

from config.celery import celery_app
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
def update_search_index(self):
    cache_key = "update_search_index"
    # 3 hours
    cache_time = 60 * 60 *3

    if cache.get(cache_key):
        return
    cache.set(cache_key, True, cache_time)

    # Run update_index --schema-only
    call_command("update_index", schema_only=True)

    # Run update_index
    call_command("update_index")

    # Clear the cache
    cache.delete(cache_key)


@celery_app.task(bind=True)
def schedule_feedback_email_notification(self):
    feedback_received = utils.feedback_received_within()
    if not feedback_received:
        return
    utils.send_feedback_notification()
