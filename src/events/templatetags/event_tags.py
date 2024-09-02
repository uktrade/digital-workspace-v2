from django import template
from events.models import EventPage

register = template.Library()


@register.simple_tag
def get_event_date(event: EventPage) -> str:
    event_date = event.event_date.strftime("%-d %B")
    start_time = event.start_time.strftime("%-I%p").lstrip("0").lower()
    end_time = event.end_time.strftime("%-I%p").lstrip("0").lower()
    return f"{event_date} {start_time}-{end_time} GMT"
