from core.utils import format_time
from events.models import EventPage


def get_event_date(event: EventPage) -> str:
    return event.event_date.strftime("%-d %B %Y")


def get_event_time(event: EventPage) -> str:
    start_time = format_time(event.start_time)
    end_time = format_time(event.end_time)
    return f"{start_time} - {end_time}"
