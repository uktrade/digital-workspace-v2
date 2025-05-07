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
    get_teams,
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

    is_active = django_filters.ChoiceFilter(
        field_name="is_active",
        widget=forms.widgets.Select(attrs={"class": "dwds-select"}),
        choices=[
            (True, "Active"),
            (False, "Inactive"),
        ],
        label="profile status",
    )
    city = django_filters.MultipleChoiceFilter(
        field_name="uk_office_location__city",
        choices=get_uk_city_locations,
        widget=forms.widgets.SelectMultiple(attrs={"class": "dwds-multiselect"}),
        label="city",
    )
    building_name = django_filters.MultipleChoiceFilter(
        field_name="uk_office_location__building_name",
        choices=get_uk_buildings,
        widget=forms.widgets.SelectMultiple(attrs={"class": "dwds-multiselect"}),
        label="office location",
    )
    grade = django_filters.MultipleChoiceFilter(
        field_name="grade__name",
        choices=get_grades,
        widget=forms.widgets.SelectMultiple(attrs={"class": "dwds-multiselect"}),
        label="grade",
    )
    professions = django_filters.MultipleChoiceFilter(
        field_name="professions__name",
        choices=get_professions,
        widget=forms.widgets.SelectMultiple(attrs={"class": "dwds-multiselect"}),
        label="professions",
    )
    key_skills = django_filters.MultipleChoiceFilter(
        field_name="key_skills__name",
        choices=get_key_skills,
        widget=forms.widgets.SelectMultiple(attrs={"class": "dwds-multiselect"}),
        label="key skills",
    )
    learning_interests = django_filters.MultipleChoiceFilter(
        field_name="learning_interests__name",
        choices=get_learning_interests,
        widget=forms.widgets.SelectMultiple(attrs={"class": "dwds-multiselect"}),
        label="learning interests",
    )
    networks = django_filters.MultipleChoiceFilter(
        field_name="networks__name",
        choices=get_networks,
        widget=forms.widgets.SelectMultiple(attrs={"class": "dwds-multiselect"}),
        label="networks",
    )
    additional_roles = django_filters.MultipleChoiceFilter(
        field_name="additional_roles__name",
        choices=get_additional_roles,
        widget=forms.widgets.SelectMultiple(attrs={"class": "dwds-multiselect"}),
        label="additional roles",
    )

    teams = django_filters.MultipleChoiceFilter(
        field_name="roles__team",
        choices=get_teams,
        widget=forms.widgets.SelectMultiple(attrs={"class": "dwds-multiselect"}),
        label="teams",
    )

    sort_by = django_filters.OrderingFilter(
        choices=[
            (choice_key, choice_value["label"])
            for choice_key, choice_value in ORDER_CHOICES.items()
        ],
        method="apply_ordering",
    )

    custom_sorters = ["sort_by"]
    custom_filters = ["is_active"]

    def apply_ordering(self, queryset, name, value) -> QuerySet[Person]:
        order_fields = ORDER_CHOICES[value[0]]["ordering"]
        return queryset.order_by(*order_fields)
