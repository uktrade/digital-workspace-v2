import requests
from celery import shared_task
from django.conf import settings
from requests_hawk import HawkAuth

from peoplefinder.models import Person
from peoplefinder.views.api.person import PersonSerializer


@shared_task
def jml_person_update(person_id):
    if not settings.JML_PERSON_UPDATE_WEBHOOK:
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
        id=settings.JML_HAWK_ID,
        key=settings.JML_HAWK_KEY,
    )
    requests.post(
        settings.JML_PERSON_UPDATE_WEBHOOK,
        auth=hawk_auth,
        data=serializer.data,
    )
