from typing import TYPE_CHECKING

from django.utils.safestring import mark_safe

from core.utils import format_time


if TYPE_CHECKING:
    from events.models import EventPage


def get_event_datetime_display_string(event: "EventPage") -> str:
    event_start_date = event.event_start.strftime("%-d %B %Y")
    event_end_date = event.event_end.strftime("%-d %B %Y")
    event_start_time = format_time(event.event_start.time())
    event_end_time = format_time(event.event_end.time())

    if event_start_date == event_end_date:
        event_post_title = mark_safe(  # noqa S308
            f"{event_start_date} <br>{event_start_time} - {event_end_time}"
        )
    else:
        event_post_title = mark_safe(  # noqa S308
            f"{event_start_date} {event_start_time} - <br>{event_end_date} {event_end_time}"
        )

    return event_post_title
