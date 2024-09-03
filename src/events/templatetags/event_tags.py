from datetime import time

from django import template

from events.models import EventPage


register = template.Library()


@register.simple_tag
def get_event_date(event: EventPage) -> str:
    return event.event_date.strftime("%-d %B %Y")


@register.simple_tag
def get_event_time(event: EventPage) -> str:
    start_time = format_time(event.start_time)
    end_time = format_time(event.end_time)
    return f"{start_time} - {end_time}"


def format_time(time_obj: time) -> str:
    if time_obj.minute == 0:
        return time_obj.strftime("%-I%p").lstrip("0").lower()
    return time_obj.strftime("%-I:%M%p").lstrip("0").lower()
