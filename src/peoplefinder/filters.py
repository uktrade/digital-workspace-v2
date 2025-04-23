import django_filters
from django import forms

from peoplefinder.utils import get_uk_city_locations


ORDER_CHOICES = [("ascending", "Ascending"), ("descending", "Descending")]


class DiscoverFilters(django_filters.FilterSet):
    city = django_filters.ChoiceFilter(
        field_name="uk_office_location__city",
        choices=get_uk_city_locations,
        widget=forms.widgets.Select(attrs={"class": "dwds-select"}),
    )
    sort_by = django_filters.OrderingFilter(
        fields=(("first_name", "first_name"), ("grade", "grade")),
        field_labels={
            "-grade": "Grade (ascending)",
        },
    )
