import django_filters
from django import forms
from django.db.models import Q, QuerySet

from core.filters import FilterSet
from peoplefinder.models import Person
from peoplefinder.services.reference import (
    get_additional_roles,
    get_grades,
    get_key_skills,
    get_professions,
    get_teams,
    get_uk_buildings,
    get_uk_city_locations,
)


ORDER_CHOICES = {
    "grade": {
        "label": "Grade",
        "ordering": ("grade", "last_name", "first_name"),
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
        empty_label="All",
        label="profile status",
    )
    display_civil_servants = django_filters.BooleanFilter(
        widget=forms.CheckboxInput,
        label="Display civil servants only",
        method="filter_non_civil_servants",
    )
    profile_completion = django_filters.ChoiceFilter(
        field_name="profile_completion",
        # widget=forms.widgets.Select(attrs={"class": "dwds-select"}),
        choices=[
            ("full", "Complete"),
            ("partial", "Incomplete"),
        ],
        label="profile completion",
        empty_label="All",
        method="filter_profile_completion",
    )

    city = django_filters.MultipleChoiceFilter(
        field_name="uk_office_location__city",
        choices=get_uk_city_locations,
        widget=forms.widgets.CheckboxSelectMultiple(),
        label="city",
    )
    building_name = django_filters.MultipleChoiceFilter(
        field_name="uk_office_location__building_name",
        choices=get_uk_buildings,
        widget=forms.widgets.CheckboxSelectMultiple(),
        label="office",
    )
    grade = django_filters.MultipleChoiceFilter(
        field_name="grade__name",
        choices=get_grades,
        widget=forms.widgets.CheckboxSelectMultiple(),
        label="grade",
    )
    professions = django_filters.MultipleChoiceFilter(
        field_name="professions__name",
        choices=get_professions,
        widget=forms.widgets.CheckboxSelectMultiple(),
        label="profession",
    )
    key_skills = django_filters.MultipleChoiceFilter(
        field_name="key_skills__name",
        choices=get_key_skills,
        widget=forms.widgets.CheckboxSelectMultiple(),
        label="key skill",
    )
    additional_roles = django_filters.MultipleChoiceFilter(
        field_name="additional_roles__name",
        choices=get_additional_roles,
        widget=forms.widgets.CheckboxSelectMultiple(),
        label="additional role",
    )
    teams = django_filters.MultipleChoiceFilter(
        choices=get_teams,
        widget=forms.widgets.CheckboxSelectMultiple(),
        label="team",
        method="filter_team_membership_and_subteams",
    )

    sort_by = django_filters.OrderingFilter(
        choices=[
            (choice_key, choice_value["label"])
            for choice_key, choice_value in ORDER_CHOICES.items()
        ],
        empty_label=None,
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

    def filter_team_membership_and_subteams(self, queryset, name, value):
        if "null" not in value:
            return queryset.filter(roles__team__children__parent__in=value)

        if "null" in value and len(value) == 1:
            return queryset.filter(roles__isnull=True)

        value.remove("null")
        no_team_selected = Q(roles__isnull=True)
        other_teams_selected = Q(roles__team__children__parent__in=value)
        return queryset.filter(no_team_selected | other_teams_selected)
