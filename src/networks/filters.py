import django_filters
from django import forms

from networks.models import Network


class NetworksFilters(django_filters.FilterSet):

    def get_network_type_choices():
        network_types = (
            Network.objects.live()
            .public()
            .exclude(network_type__isnull=True)
            .values_list("network_type", flat=True)
            .distinct()
        )
        return [
            (network_type, Network.NetworkTypes(network_type).label)
            for network_type in network_types
        ]

    network_type = django_filters.ChoiceFilter(
        field_name="network_type",
        choices=get_network_type_choices(),
        lookup_expr="exact",
        widget=forms.widgets.Select(attrs={"class": "dwds-select"}),
        empty_label="All network types",
    )
