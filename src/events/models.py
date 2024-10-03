from datetime import datetime as dt
from datetime import timedelta

from django.db import models
from django.utils import timezone
from wagtail.admin.panels import FieldPanel, FieldRowPanel, MultiFieldPanel

from content.models import BasePage, ContentPage
from core.models import fields
from events import types
from events.utils import get_event_start_date, get_event_end_date, get_event_start_time, get_event_end_time


class EventsHome(BasePage):
    template = "events/events_home.html"
    show_in_menus = True
    is_creatable = False
    subpage_types = ["events.EventPage"]

    def get_template(self, request, *args, **kwargs):
        return self.template

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        events = EventPage.objects.live().public()
        context["events"] = events

        return context


class EventPage(ContentPage):
    is_creatable = True
    parent_page_types = ["events.EventsHome"]
    template = "events/event_page.html"

    event_start = models.DateTimeField(
        help_text="Start date/time of the event.",
    )
    event_end = models.DateTimeField(
        help_text="End date/time of the event.",
    )
    online_event_url = fields.URLField(
        blank=True,
        null=True,
        verbose_name="Online event link",
        help_text="If the event is online, you can add a link here for others to join.",
    )
    offline_event_url = fields.URLField(
        blank=True,
        null=True,
        verbose_name="In person registration link",
        help_text="If the event is in person, you can add a link here for registration.",
    )
    submit_questions_url = fields.URLField(
        blank=True,
        null=True,
        verbose_name="Submit questions link",
        help_text="Link to a page for others to submit their questions.",
    )
    event_recording_url = fields.URLField(
        blank=True,
        null=True,
        verbose_name="View event recording link",
        help_text="Optional link to a page for others to view the recorded event.",
    )
    event_type = models.CharField(
        choices=types.EventType.choices,
        default=types.EventType.ONLINE,
    )
    audience = models.CharField(
        choices=types.EventAudience.choices,
        blank=True,
        null=True,
    )
    location = models.ForeignKey(
        "peoplefinder.UkStaffLocation",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="If you don't select a location the page will show 'Location: To be confirmed'",
    )
    room = models.CharField(
        blank=True,
        null=True,
    )
    room_capacity = models.IntegerField(
        blank=True,
        null=True,
    )

    content_panels = ContentPage.content_panels + [
        MultiFieldPanel(
            [
                FieldRowPanel(
                    [
                        FieldPanel("event_start"),
                        FieldPanel("event_end"),
                    ]
                ),
            ],
            heading="Date/Time details",
        ),
        FieldPanel("event_type"),
        MultiFieldPanel(
            [
                FieldPanel("location"),
                FieldRowPanel(
                    [
                        FieldPanel("room"),
                        FieldPanel("room_capacity"),
                    ]
                ),
                FieldPanel("offline_event_url"),
            ],
            heading="In person details",
        ),
        MultiFieldPanel(
            [
                FieldPanel("online_event_url"),
            ],
            heading="Online details",
        ),
        FieldPanel("audience"),
        FieldPanel("submit_questions_url"),
        FieldPanel("event_recording_url"),
    ]

    def get_template(self, request, *args, **kwargs):
        return self.template

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        context.update(
            is_online=self.event_type == types.EventType.ONLINE,
            is_in_person=self.event_type == types.EventType.IN_PERSON,
            is_hybrid=self.event_type == types.EventType.HYBRID,
            event_start_date=get_event_start_date(self),
            event_start_time=get_event_start_time(self),
            event_end_date=get_event_end_date(self),
            event_end_time=get_event_end_time(self),
        )

        return context

    @property
    def is_past_event(self) -> bool:
        adjusted_datetime = timezone.make_aware(
            self.event_end + timedelta(hours=1) # Check if/why we need +timedelta maybe
        )
        return timezone.now() > adjusted_datetime
