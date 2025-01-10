from django.forms import Form
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import FormView
from wagtail.models import Page

from networks.models import Network, NetworkContentPage
from networks.utils import (
    convert_network_content_page_to_network,
    convert_network_to_content_page,
    convert_network_to_networks_home,
)


# TODO: Remove as part of INTR-517
class ConvertPageView(FormView):
    template_name = "networks/admin/are_you_sure.html"
    form_class = Form

    irreversible: bool = False
    operation: str = ""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect("wagtailadmin_home")
        pk = kwargs.get("pk")
        self.page = Page.objects.get(pk=pk)
        self.parent_pk = self.page.get_parent().pk
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        return redirect("wagtailadmin_explore", parent_page_id=self.parent_pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = reverse(
            "wagtailadmin_explore", kwargs={"parent_page_id": self.parent_pk}
        )
        context["irreversible"] = self.irreversible
        context["operation"] = self.operation
        return context


# TODO: Remove as part of INTR-517
class ConvertNetworkToNetworkContentPageView(ConvertPageView):
    operation = "Convert to Network Content Page"

    def form_valid(self, form):
        network: Network = self.page.specific
        convert_network_to_content_page(network)
        return super().form_valid(form)


# TODO: Remove as part of INTR-517
class ConvertNetworkToNetworksHomeView(ConvertPageView):
    operation = "Convert to Networks Home"

    def form_valid(self, form):
        network: Network = self.page.specific
        convert_network_to_networks_home(network)
        return super().form_valid(form)


# TODO: Remove as part of INTR-517
class ConvertNetworkContentPageToNetworkPageView(ConvertPageView):
    operation = "Convert to Network Page"
    irreversible = True

    def form_valid(self, form):
        network_content_page: NetworkContentPage = self.page.specific
        convert_network_content_page_to_network(network_content_page)
        return super().form_valid(form)
