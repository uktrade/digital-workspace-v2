import requests
from celery import shared_task
from django.conf import settings
from requests_hawk import HawkAuth

from config.celery import celery_app
from peoplefinder.models import Person
from peoplefinder.views.api.person import PersonSerializer


@shared_task
def person_update_notifier(person_id):
    if not settings.PERSON_UPDATE_WEBHOOK_URL:
        return

    person = (
        Person.objects.get_annotated()
        .defer(
            "photo",
            "do_not_work_for_dit",
        )
        .get(pk=person_id)
    )

    serializer = PersonSerializer(person)

    hawk_auth = HawkAuth(
        id=settings.PERSON_UPDATE_HAWK_ID,
        key=settings.PERSON_UPDATE_HAWK_KEY,
    )
    requests.post(
        settings.PERSON_UPDATE_WEBHOOK_URL,
        auth=hawk_auth,
        data=serializer.data,
        timeout=5,
    )


@celery_app.task(bind=True)
def notify_user_about_profile_changes(self, person_pk, personalisation):
    from peoplefinder.services.person import PersonService

    PersonService().notify_about_changes_debounce(
        person_pk=person_pk,
        personalisation=personalisation,
        countdown=self.request.kwargs.get("countdown"),
    )
