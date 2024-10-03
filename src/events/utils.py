from typing import TYPE_CHECKING

from core.utils import format_time
from datetime import datetime as dt


if TYPE_CHECKING:
    from events.models import EventPage


def get_event_start_date(event: "EventPage") -> str:
    return f"{event.event_start.strftime("%-d %B %Y")}"


def get_event_end_date(event: "EventPage") -> str:
    return f"{event.event_end.strftime("%-d %B %Y")}"


def get_event_start_time(event: "EventPage") -> str:
    return format_time(event.event_start.time())


def get_event_end_time(event: "EventPage") -> str:
    return format_time(event.event_end.time())
