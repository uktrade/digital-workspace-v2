import django_filters
from django import forms

from peoplefinder.utils import get_uk_city_locations


ORDER_CHOICES = (("ascending", "Ascending"), ("descending", "Descending"))


class DiscoverFilters(django_filters.FilterSet):
    def filter_by_order(self, queryset, field_name, value):
        expression = field_name if value == "ascending" else f"-{field_name}"
        return queryset.order_by(expression)

    sort_by_first_name = django_filters.ChoiceFilter(
        field_name="first_name",
        label="sort_by_first_name",
        choices=ORDER_CHOICES,
        method="filter_by_order",
    )
    sort_by_grade = django_filters.ChoiceFilter(
        field_name="grade",
        label="sort_by_grade",
        choices=ORDER_CHOICES,
        method="filter_by_order",
    )
    sort_by = django_filters.OrderingFilter(
        fields=(("first_name", "first_name"), ("grade", "grade")),
    )

    city = django_filters.ChoiceFilter(
        field_name="uk_office_location__city",
        choices=get_uk_city_locations,
        widget=forms.widgets.Select(attrs={"class": "dwds-select"}),
    )
