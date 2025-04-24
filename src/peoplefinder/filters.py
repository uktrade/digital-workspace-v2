import django_filters
from django import forms

from core.filters import FilterSet
from peoplefinder.utils import get_uk_city_locations


class DiscoverFilters(FilterSet):
    city = django_filters.ChoiceFilter(
        field_name="uk_office_location__city",
        choices=get_uk_city_locations,
        widget=forms.widgets.Select(attrs={"class": "dwds-select"}),
    )
