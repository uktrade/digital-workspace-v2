import django_filters
from django import forms

from core.filters import FilterSet
from events import types
from peoplefinder.services.uk_staff_locations import UkStaffLocationService


EVENT_TYPE_ALL_VALUE = ""
EVENT_TYPE_CHOICES = [
    (EVENT_TYPE_ALL_VALUE, "All"),
    (types.EventType.IN_PERSON, "In-person"),
    (types.EventType.ONLINE, "Online"),
]


class EventsFilters(FilterSet):
    event_type = django_filters.ChoiceFilter(
        method="event_format_filter",
        choices=EVENT_TYPE_CHOICES,
        widget=forms.widgets.RadioSelect(
            attrs={"class": "dwds-radios content-switcher"}
        ),
        empty_label=None,
    )

    location = django_filters.ChoiceFilter(
        field_name="location__city",
        choices=[
            (c, c) for c in UkStaffLocationService().get_uk_staff_location_cities()
        ],
        lookup_expr="exact",
        widget=forms.widgets.Select(attrs={"class": "dwds-select width-full"}),
        empty_label="All locations",
    )

    def event_format_filter(self, queryset, name, value):
        if value == EVENT_TYPE_ALL_VALUE:
            return queryset

        event_types = [types.EventType.HYBRID]
        event_types.append(types.EventType(value))

        return queryset.filter(event_type__in=event_types)
