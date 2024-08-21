from django.db import models
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, FieldRowPanel

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
    event_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="Online event url",
        help_text="If the event is online, you can add a link here for others to join."
    )
    submit_questions_url = models.URLField(
        blank=True,
        null=True,
        help_text="Link to a page for others to submit their questions."
    )
    audience = models.CharField(
        choices=types.EventAudience.choices,
        default=types.EventAudience.ALL_STAFF,
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
    room_capacity = models.IntegerField(blank=True, null=True,)

    in_person_only = models.BooleanField(
        default=False,
        verbose_name="In person only event?",
        help_text="Tick this box if this event is being held in person only.",
    )

    content_panels = ContentPage.content_panels + [
        MultiFieldPanel([
            FieldPanel("event_date"),
            FieldRowPanel([
                FieldPanel("start_time"),
                FieldPanel("end_time"),
            ]),
        ], heading="Date/Time details"),
        FieldPanel("event_url"),
        FieldPanel("submit_questions_url"),
        FieldPanel("audience"),
        MultiFieldPanel([
            FieldPanel("location"),
            FieldRowPanel([
                FieldPanel("room"),
                FieldPanel("room_capacity"),
            ]),     
        ], heading="Location details"),
        FieldPanel("in_person_only"),
    ]

    # indexed_fields = []

    def get_template(self, request, *args, **kwargs):
        return self.template

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        return context
