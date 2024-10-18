from datetime import timedelta

from django.http import HttpResponse
from django.utils import timezone
from icalendar import Calendar, Event, vCalAddress, vText

from .models import EventPage


def generate_dummy_event() -> Event:
    now = timezone.now()
    start = now + timedelta(minutes=10)
    end = start + timedelta(minutes=60)
    event = Event()
    event.add("summary", "'10 minutes from now' dummy event")
    event.add("dtstart", start)
    event.add("dtend", end)
    event.add("dtstamp", now)

    organiser = vCalAddress("MAILTO:poc@ical.eg")
    organiser.params["cn"] = vText("Marcel K")
    event["organizer"] = organiser

    # just made-up but stays consistent so clients update rather
    # than add a new one
    uid = "20050115T101010/27346262376@mxm.dk"
    event["uid"] = uid
    event.add("priority", 5)

    event["location"] = vText("North Pole")
    return event


def to_ical(event: EventPage) -> Event:
    ical_event = Event()

    ical_event["uid"] = event.pk
    ical_event.add("summary", event.title)
    ical_event.add("dtstart", event.event_start)
    ical_event.add("dtend", event.event_end)
    ical_event.add("dtstamp", event.last_published_at)

    ical_event.add(
        "description", f"<a href='{event.url}'>For details see event listing</a>"
    )
    if event.location:
        ical_event["location"] = event.location.name
    ical_event.add("priority", 5)

    author = event.get_first_publisher()
    organiser = vCalAddress(f"MAILTO:{author.profile.preferred_email}")
    organiser.params["cn"] = vText(author.profile.full_name)
    ical_event["organizer"] = organiser

    return ical_event


def ical_feed(request):
    cal = Calendar()
    cal.add("prodid", "-//intranet-all-events//dbt.gov.uk//")
    cal.add("version", "2.0")

    cal.add_component(generate_dummy_event())  # add a dummy event to test updating

    # add all events for now - should probably be a personalised
    # list, and we could generate the ical data on save, making
    # this just be a values query joined, for speed
    for event in EventPage.objects.all():
        cal.add_component(to_ical(event))

    return HttpResponse(
        cal.to_ical().decode("utf-8"),
        content_type="text/calendar",
    )
