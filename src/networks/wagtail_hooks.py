from django.urls import reverse
from wagtail import hooks
from wagtail.admin import widgets as wagtailadmin_widgets

from networks.models import Network, NetworkContentPage
from networks.views import NetworkChooserViewSet


@hooks.register("register_page_listing_more_buttons")
def page_listing_more_buttons(page, page_perms, is_parent=False):
    if isinstance(page, Network):
        yield wagtailadmin_widgets.PageListingButton(
            "Convert to Network Content Page",
            reverse("networks:convert-network-to-content-page", kwargs={"pk": page.pk}),
            priority=10,
        )
        yield wagtailadmin_widgets.PageListingButton(
            "Convert to Networks Home",
            reverse(
                "networks:convert-network-to-networks-home", kwargs={"pk": page.pk}
            ),
            priority=10,
        )
    if isinstance(page, NetworkContentPage):
        yield wagtailadmin_widgets.PageListingButton(
            "Convert to Network",
            reverse(
                "networks:convert-network-content-page-to-network",
                kwargs={"pk": page.pk},
            ),
            priority=10,
        )


@hooks.register("register_admin_viewset")
def register_network_chooser_viewset():
    return NetworkChooserViewSet("network_chooser", url_prefix="network-chooser")
