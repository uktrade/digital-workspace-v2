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
    display_civil_servants = django_filters.BooleanFilter(
        widget=forms.CheckboxInput,
        label="Display civil servants only",
        method="filter_non_civil_servants",
    )
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
        null_label="Not set",
        widget=forms.widgets.CheckboxSelectMultiple(),
        label="city",
    )
    building_name = django_filters.MultipleChoiceFilter(
        field_name="uk_office_location__building_name",
        choices=get_uk_buildings,
        null_label="Not set",
        widget=forms.widgets.CheckboxSelectMultiple(),
        label="office",
    )
    grade = django_filters.MultipleChoiceFilter(
        field_name="grade__name",
        choices=get_grades,
        null_label="Not set",
        widget=forms.widgets.CheckboxSelectMultiple(),
        label="grade",
    )
    professions = django_filters.MultipleChoiceFilter(
        field_name="professions__name",
        choices=get_professions,
        null_label="Not set",
        widget=forms.widgets.CheckboxSelectMultiple(),
        label="profession",
    )
    key_skills = django_filters.MultipleChoiceFilter(
        field_name="key_skills__name",
        choices=get_key_skills,
        null_label="Not set",
        widget=forms.widgets.CheckboxSelectMultiple(),
        label="key skill",
    )
    learning_interests = django_filters.MultipleChoiceFilter(
        field_name="learning_interests__name",
        choices=get_learning_interests,
        null_label="Not set",
        widget=forms.widgets.CheckboxSelectMultiple(),
        label="learning interest",
    )
    networks = django_filters.MultipleChoiceFilter(
        field_name="networks__name",
        choices=get_networks,
        null_label="Not set",
        widget=forms.widgets.CheckboxSelectMultiple(),
        label="network",
    )
    additional_roles = django_filters.MultipleChoiceFilter(
        field_name="additional_roles__name",
        choices=get_additional_roles,
        null_label="Not set",
        widget=forms.widgets.CheckboxSelectMultiple(),
        label="additional role",
    )
    profile_completion = django_filters.ChoiceFilter(
        field_name="profile_completion",
        # widget=forms.widgets.Select(attrs={"class": "dwds-select"}),
        choices=[
            ("full", "Complete"),
            ("partial", "Incomplete"),
        ],
        label="profile completion",
        method="filter_profile_completion",
    )

    teams = django_filters.MultipleChoiceFilter(
        field_name="roles__team__name",
        choices=get_teams,
        null_label="Not set",
        widget=forms.widgets.CheckboxSelectMultiple(),
        label="team",
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
    checkbox_filters = ["display_civil_servants"]

    def apply_ordering(self, queryset, name, value) -> QuerySet[Person]:
        order_fields = ORDER_CHOICES[value[0]]["ordering"]
        return queryset.order_by(*order_fields)

    def filter_non_civil_servants(self, queryset, name, value) -> QuerySet[Person]:
        if value:
            return queryset.exclude(grade__code="non_graded_contractor")
        return queryset

    def filter_profile_completion(self, queryset, name, value) -> QuerySet[Person]:
        if value == "full":
            return queryset.filter(profile_completion__gte=100)

        return queryset.filter(profile_completion__lt=100)
