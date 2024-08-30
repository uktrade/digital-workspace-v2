from django import template
from events.models import EventPage
from datetime import datetime

register = template.Library()

@register.simple_tag
def get_event_date(event: EventPage) -> str:
    # TODO: format string to become a date
    # event_date = datetime(event.event_date.strftime("%d %b %Y"))
    return f"{event.event_date}, {event.start_time}-{event.end_time} GMT"
