import django_filters
from django import forms

from peoplefinder.utils import get_uk_city_locations


ORDER_CHOICES = (("ascending", "Ascending"), ("descending", "Descending"))


class DiscoverFilters(django_filters.FilterSet):
    def filter_by_order(self, queryset, field_name, value):
        expression = field_name if value == "ascending" else f"-{field_name}"
        return queryset.order_by(expression)

    order_by_first_name = django_filters.ChoiceFilter(
        field_name="first_name",
        label="order_by_name",
        choices=ORDER_CHOICES,
        method="filter_by_order",
    )

    city = django_filters.ChoiceFilter(
        field_name="uk_office_location__city",
        choices=get_uk_city_locations,
        widget=forms.widgets.Select(attrs={"class": "dwds-select"}),
    )
