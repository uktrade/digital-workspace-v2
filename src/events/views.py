from datetime import timedelta

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
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
    ical_event.add("summary", "Anonymous event title")
    ical_event.add("dtstart", event.event_start)
    ical_event.add("dtend", event.event_end)
    ical_event.add("dtstamp", event.last_published_at)

    ical_event.add("description", f"See event listing: {event.url}")
    # Anonymised for reduced risk during testing
    # if event.location:
    #     ical_event["location"] = event.location.name
    ical_event.add("priority", 5)

    # Anonymised for reduced risk during testing
    # author = event.get_first_publisher()
    # organiser = vCalAddress(f"MAILTO:{author.profile.preferred_email}")
    # organiser.params["cn"] = vText(author.profile.full_name)
    # ical_event["organizer"] = organiser

    return ical_event


def get_user_token(user):
    if existing_token := user.profile.ical_token:
        return existing_token

    token = get_random_string(length=80)
    user.profile.ical_token = token
    user.profile.save()
    return token


def ical_links(request):
    token = get_user_token(request.user)
    feed_url = request.build_absolute_uri(reverse("ical_feed"))
    full_uri = f"{feed_url}?tk={token}&u={request.user.profile.slug}"
    full_uri_encoded = f"{feed_url}%3Ftk={token}%26u={request.user.profile.slug}"
    return render(
        request,
        "events/calendar_links.html",
        {
            "token": token,
            "raw_uri": full_uri,
            "encoded_uri": full_uri_encoded,
        },
    )


# This end point needs to be covered by a unique auth mechanism to allow calendar
# clients to update their feeds without SSO; it uses a token and ought to be
# behind the VPN protection as well
def ical_feed(request):
    user = request.user
    token = request.GET.get("tk", None)
    if user.is_anonymous:
        uuid = request.GET.get("u", None)
        user = get_user_model().objects.get(profile__slug=uuid)

    if user is None or token != get_user_token(user):
        return HttpResponse("Unauthorized", status=401)

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
