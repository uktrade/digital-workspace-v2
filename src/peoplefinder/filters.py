import django_filters
from django import forms

from peoplefinder.utils import (
    get_additional_roles,
    get_grades,
    get_key_skills,
    get_learning_interests,
    get_networks,
    get_professions,
    get_uk_buildings,
    get_uk_city_locations,
)


class DiscoverFilters(django_filters.FilterSet):
    city = django_filters.ChoiceFilter(
        field_name="uk_office_location__city",
        choices=get_uk_city_locations,
        widget=forms.widgets.Select(attrs={"class": "dwds-select"}),
    )
    building_name = django_filters.ChoiceFilter(
        field_name="uk_office_location__building_name",
        choices=get_uk_buildings,
        widget=forms.widgets.Select(attrs={"class": "dwds-select"}),
    )
    grade = django_filters.ChoiceFilter(
        field_name="grade__name",
        choices=get_grades,
        widget=forms.widgets.Select(attrs={"class": "dwds-select"}),
    )
    professions = django_filters.ChoiceFilter(
        field_name="professions__name",
        choices=get_professions,
        widget=forms.widgets.Select(attrs={"class": "dwds-select"}),
    )
    key_skills = django_filters.ChoiceFilter(
        field_name="key_skills__name",
        choices=get_key_skills,
        widget=forms.widgets.Select(attrs={"class": "dwds-select"}),
    )
    learning_interests = django_filters.ChoiceFilter(
        field_name="learning_interests__name",
        choices=get_learning_interests,
        widget=forms.widgets.Select(attrs={"class": "dwds-select"}),
    )
    networks = django_filters.ChoiceFilter(
        field_name="networks__name",
        choices=get_networks,
        widget=forms.widgets.Select(attrs={"class": "dwds-select"}),
    )
    additional_roles = django_filters.ChoiceFilter(
        field_name="additional_roles__name",
        choices=get_additional_roles,
        widget=forms.widgets.Select(attrs={"class": "dwds-select"}),
    )
