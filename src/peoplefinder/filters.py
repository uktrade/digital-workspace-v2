import django_filters
from django import forms

from peoplefinder.utils import get_uk_buildings, get_uk_locations


class DiscoverFilters(django_filters.FilterSet):
    building_name = django_filters.ChoiceFilter(
        field_name="uk_office_location__building_name",
        choices=get_uk_buildings,
        widget=forms.widgets.Select(
            attrs={"class": "dwds-select", "style": "padding-right: 0"}
        ),
    )

    city = django_filters.ChoiceFilter(
        field_name="uk_office_location__city",
        choices=get_uk_locations,
        widget=forms.widgets.Select(attrs={"class": "dwds-select"}),
    )
