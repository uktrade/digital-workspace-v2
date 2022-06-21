import requests
from celery import shared_task
from django.conf import settings
from requests_hawk import HawkAuth

from peoplefinder.models import Person
from peoplefinder.views.api.person import PersonSerializer


@shared_task
def person_update_notifier(person_id):
    if not settings.PERSON_UPDATE_WEBHOOK_URL:
        return

    person = (
        Person.objects.get_annotated()
        .with_profile_completion()
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
    )
