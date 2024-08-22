from django.db import models
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
    parent_page_types = ["events.EventsHome", "events.EventPage"]
    template = "events/event_page.html"

    event_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    online_event_url = models.URLField(
        blank=True,
        null=True,
        help_text="If the event is online, you can add a link here for others to join.",
    )
    offline_event_url = models.URLField(
        blank=True,
        null=True,
        help_text="If the event is offline, you can add a link here for registration.",
    )
    submit_questions_url = models.URLField(
        blank=True,
        null=True,
        help_text="Link to a page for others to submit their questions.",
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
    ]

    # indexed_fields = []

    def get_template(self, request, *args, **kwargs):
        return self.template

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        return context
