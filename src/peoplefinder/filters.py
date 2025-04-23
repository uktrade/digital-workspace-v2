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

    def filter_by_order(self, queryset, field_name, value):
        expression = field_name if value == "ascending" else f"-{field_name}"
        return queryset.order_by(expression)

    @property
    def qs(self):
        qs = super().qs
        order_list = []

        grade_sort = self.form.cleaned_data.get("sort_by_grade")
        first_name_sort = self.form.cleaned_data.get("sort_by_first_name")

        if grade_sort:
            expression = "grade" if grade_sort == "ascending" else "-grade"
            order_list.append(expression)
        if first_name_sort:
            expression = (
                "first_name" if first_name_sort == "ascending" else "-first_name"
            )
            order_list.append(expression)
        if order_list:
            qs = qs.order_by(*order_list)
        return qs
