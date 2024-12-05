from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from django.db import models
from django.http import Http404
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils import timezone
from wagtail.admin.panels import FieldRowPanel, MultiFieldPanel
from wagtail.contrib.routable_page.models import RoutablePageMixin, route

from content.models import BasePage, ContentPage
from core.models import fields
from core.panels import FieldPanel
from events import types
from events.utils import get_event_datetime_display_string


class EventsHome(RoutablePageMixin, BasePage):
    template = "events/events_home.html"
    show_in_menus = True
    is_creatable = False
    subpage_types = ["events.EventPage"]

    def get_template(self, request, *args, **kwargs):
        return self.template

    @route(r"^(?P<year>\d{4})/$", name="month_year")
    def year_events(self, request, year):
        return redirect(
            self.full_url + self.reverse_subpage("month_events", args=(year, 1))
        )

    @route(r"^(?P<year>\d{4})/(?P<month>\d{1,2})/$", name="month_events")
    def month_events(self, request, year, month):
        year = int(year)
        month = int(month)

        if month < 1 or month > 12:
            raise Http404

        filter_date = datetime(int(year), int(month), 1)

        return TemplateResponse(
            request,
            self.get_template(request),
            self.get_context(request, filter_date=filter_date),
        )

    def get_context(self, request, *args, **kwargs):
        from events.filters import EventsFilters

        context = super().get_context(request, *args, **kwargs)
        now = timezone.now()

        filter_date = kwargs.get("filter_date", now).date()

        month_start = filter_date.replace(day=1)

        previous_month = month_start - relativedelta(months=1)
        next_month = month_start + relativedelta(months=1)

        month_end = month_start.replace(month=next_month.month)
        if next_month.month == 1:
            month_end = month_end.replace(year=month_end.year + 1)

        events = (
            EventPage.objects.live()
            .public()
            .filter(
                event_start__gte=month_start,
                event_start__lt=month_end,
            )
            .order_by("event_start")
        )

        current_month_start = now.date().replace(day=1)

        page_title_prefix = "What's on in"
        if filter_date < current_month_start:
            page_title_prefix = "What happened in"

        # Filtering events
        events_filters = EventsFilters(request.GET, queryset=events)
        events = events_filters.qs

        context.update(
            events_filters=events_filters,
            page_title=f"{page_title_prefix} {month_start.strftime('%B %Y')}",
            upcoming_events=events.filter(
                event_start__gt=now,
            ),
            ongoing_events=events.filter(
                event_start__lte=now,
                event_end__gt=now,
            ),
            past_events=events.filter(
                event_end__lte=now,
            ),
            current_month=month_start,
            next_month=next_month,
            previous_month=previous_month,
        )
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

        is_online = self.event_type in {
            types.EventType.ONLINE,
            types.EventType.HYBRID,
        }
        is_in_person = self.event_type in {
            types.EventType.IN_PERSON,
            types.EventType.HYBRID,
        }

        context.update(
            is_online=is_online,
            is_in_person=is_in_person,
            event_date_range=get_event_datetime_display_string(self),
        )

        return context

    @property
    def is_past_event(self) -> bool:
        adjusted_datetime = self.event_end + timedelta(hours=1)
        return timezone.now() > adjusted_datetime
