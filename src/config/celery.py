import os

from celery import Celery
from celery.schedules import crontab


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

celery_app = Celery("DjangoCelery")
celery_app.config_from_object("django.conf:settings", namespace="CELERY")
celery_app.autodiscover_tasks()


celery_app.conf.beat_schedule = {
    # Staff location ingest task
    # TODO: Uncomment this when the Staff Location DB is ready.
    # "ingest-uk-staff-locations": {
    #     "task": "core.tasks.ingest_uk_staff_locations",
    #     "schedule": crontab(minute="0", hour="3"),
    # },
    # Daily feedback email task
    "schedule-feedback-email-notification": {
        "task": "core.tasks.schedule_feedback_email_notification",
        "schedule": crontab(hour=6, minute=0),
    },
    "ingest_uk_office_locations": {
        "task": "core.tasks.ingest_uk_office_locations",
        "schedule": crontab(hour=6, minute=10),
    },
    "ingest_dbt_sectors": {
        "task": "core.tasks.ingest_dbt_sectors",
        "schedule": crontab(hour=6, minute=20),
    },
}
