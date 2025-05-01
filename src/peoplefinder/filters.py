import django_filters
from django import forms
from django.db.models import QuerySet

from core.filters import FilterSet
from peoplefinder.models import Person
from peoplefinder.services.reference import (
    get_additional_roles,
    get_grades,
    get_key_skills,
    get_learning_interests,
    get_networks,
    get_professions,
    get_uk_buildings,
    get_uk_city_locations,
)


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
    is_civil_servant = django_filters.ChoiceFilter(
        field_name="grade__name",
        choices=[("Civil servants only", "Civil servants only")],
        widget=forms.widgets.Select(attrs={"class": "dwds-select"}),
        label="civil servants only",
        method="filter_non_civil_servants",
    )
    city = django_filters.ChoiceFilter(
        field_name="uk_office_location__city",
        choices=get_uk_city_locations,
        widget=forms.widgets.Select(attrs={"class": "dwds-select"}),
        label="city",
    )
    building_name = django_filters.ChoiceFilter(
        field_name="uk_office_location__building_name",
        choices=get_uk_buildings,
        widget=forms.widgets.Select(attrs={"class": "dwds-select"}),
        label="office location",
    )
    grade = django_filters.ChoiceFilter(
        field_name="grade__name",
        choices=get_grades,
        widget=forms.widgets.Select(attrs={"class": "dwds-select"}),
        label="grade",
    )
    professions = django_filters.ChoiceFilter(
        field_name="professions__name",
        choices=get_professions,
        widget=forms.widgets.Select(attrs={"class": "dwds-select"}),
        label="profession",
    )
    key_skills = django_filters.ChoiceFilter(
        field_name="key_skills__name",
        choices=get_key_skills,
        widget=forms.widgets.Select(attrs={"class": "dwds-select"}),
        label="key skills",
    )
    learning_interests = django_filters.ChoiceFilter(
        field_name="learning_interests__name",
        choices=get_learning_interests,
        widget=forms.widgets.Select(attrs={"class": "dwds-select"}),
        label="learning interests",
    )
    networks = django_filters.ChoiceFilter(
        field_name="networks__name",
        choices=get_networks,
        widget=forms.widgets.Select(attrs={"class": "dwds-select"}),
        label="networks",
    )
    additional_roles = django_filters.ChoiceFilter(
        field_name="additional_roles__name",
        choices=get_additional_roles,
        widget=forms.widgets.Select(attrs={"class": "dwds-select"}),
        label="additional roles",
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

    def filter_non_civil_servants(self, queryset, name, value) -> QuerySet[Person]:
        if value == "Civil servants only":
            return queryset.exclude(grade__code="non_graded_contractor")
        return queryset
