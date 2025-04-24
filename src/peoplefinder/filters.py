import django_filters
from django import forms
from django.db.models import QuerySet

from core.filters import FilterSet
from peoplefinder.models import Person
from peoplefinder.utils import get_uk_city_locations


ORDER_CHOICES = {
    "grade": {
        "label": "Grade",
        "ordering": ("grade", "first_name", "last_name"),
    },
    "first_name": {
        "label": "First name",
        "ordering": ("first_name", "last_name"),
    },
    "last_name": {
        "label": "Last name",
        "ordering": ("last_name", "first_name"),
    },
}


class DiscoverFilters(FilterSet):
    city = django_filters.ChoiceFilter(
        field_name="uk_office_location__city",
        choices=get_uk_city_locations,
        widget=forms.widgets.Select(attrs={"class": "dwds-select"}),
    )
    sort_by = django_filters.OrderingFilter(
        choices=[
            (choice_key, choice_value["label"])
            for choice_key, choice_value in ORDER_CHOICES.items()
        ],
        method="apply_ordering",
    )

    def apply_ordering(self, queryset, name, value) -> QuerySet[Person]:
        order_fields = ORDER_CHOICES[value[0]]["ordering"]
        return queryset.order_by(*order_fields)
