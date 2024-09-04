from datetime import time

from events.models import EventPage


def format_time(time_obj: time) -> str:
    """
    Build a time string that shows the needed information.

    Returns:
     - If there are minutes on the hour: `10:30` -> `10:30am`
     - If there are not minutes on the hour: `10:00` -> `10am`

    """
    if time_obj.minute == 0:
        return time_obj.strftime("%-I%p").lstrip("0").lower()
    return time_obj.strftime("%-I:%M%p").lstrip("0").lower()


def get_event_date(event: EventPage) -> str:
    return event.event_date.strftime("%-d %B %Y")


def get_event_time(event: EventPage) -> str:
    start_time = format_time(event.start_time)
    end_time = format_time(event.end_time)
    return f"{start_time} - {end_time}"
