import django_filters
from django import forms
from networks.models import Network

class NetworksFilters(django_filters.FilterSet):
    network_type = django_filters.ChoiceFilter(
        field_name="network_type",
        choices=Network.NetworkTypes,
        lookup_expr="exact",
        widget=forms.widgets.Select(attrs={"class": "dwds-select"}),
        empty_label="All network types",
    )
