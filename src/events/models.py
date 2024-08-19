from config.settings.base import INGESTED_MODELS_DATABASES
from content.models import ContentPage
from extended_search.index import IndexedField
from django.db import models

from peoplefinder.models import Grade


class EventsPage(ContentPage):
    is_creatable = True
    parent_page_types = ["events.EventsHome"]
    template = ""
   
    indexed_fields = [
        IndexedField(
            "description",
            tokenized=True,
            explicit=True,
        ),
        IndexedField(
            "body",
            tokenized=True,
            explicit=True,
        ),
    ]
    event_date = models.DateTimeField()
    event_url = models.URLField(
        blank=True,
        null=True,
    )

    # TODO: wip - not sure about these.
    stuff_grades = ["All stuff", Grade.objects.in_bulk(field_name="code")]
    audience = models.Choices(stuff_grades, default="All stuff")
    all_locations = ["online", INGESTED_MODELS_DATABASES["uk_staff_locations"]]
    location = models.Choices(all_locations, blank=True, null=True)

    submit_questions_url = models.URLField(
        blank=True,
        null=True,
    )

