import django_filters
from django import forms

from peoplefinder.models import Person, UkStaffLocation


class DiscoverFilters(django_filters.FilterSet):
    uk_office_location = django_filters.ModelChoiceFilter(
        queryset=UkStaffLocation.objects.all(),
        widget=forms.widgets.Select(attrs={"class": "dwds-select"}),
        empty_label=None,
    )

    class Meta:
        model = Person
        fields = ["uk_office_location"]
