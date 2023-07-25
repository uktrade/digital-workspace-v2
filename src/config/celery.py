import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

celery_app = Celery("DjangoCelery")
celery_app.config_from_object("django.conf:settings", namespace="CELERY")
celery_app.autodiscover_tasks()


celery_app.conf.beat_schedule = {
    # Nightly ingest tasks.
    "ingest-uk-staff-locations": {
        "task": "core.tasks.ingest_uk_staff_locations",
        "schedule": crontab(minute="0", hour="3"),
    },
}
