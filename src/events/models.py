from datetime import datetime as dt
from datetime import timedelta

from django.db import models
from django.utils import timezone
from wagtail.admin.panels import FieldPanel, FieldRowPanel, MultiFieldPanel

from content.models import BasePage, ContentPage
from events import types


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

    event_date = models.DateField(
        help_text="Date and time should be entered based on the time in London/England.",
    )
    start_time = models.TimeField()
    end_time = models.TimeField()
    online_event_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="Online event link",
        help_text="If the event is online, you can add a link here for others to join.",
    )
    offline_event_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="In person registration link",
        help_text="If the event is in person, you can add a link here for registration.",
    )
    submit_questions_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="Submit questions link",
        help_text="Link to a page for others to submit their questions.",
    )
    event_recording_url = models.URLField(
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
                FieldPanel("event_date"),
                FieldRowPanel(
                    [
                        FieldPanel("start_time"),
                        FieldPanel("end_time"),
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
            is_online=self.event_type
            in [types.EventType.ONLINE, types.EventType.HYBRID],
            is_in_person=self.event_type
            in [types.EventType.IN_PERSON, types.EventType.HYBRID],
        )

        return context

    @property
    def is_past_event(self) -> bool:
        adjusted_datetime = timezone.make_aware(
            dt.combine(self.event_date, self.end_time) + timedelta(hours=1)
        )
        return timezone.now() > adjusted_datetime