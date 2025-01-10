from django.urls import reverse
from wagtail import hooks
from wagtail.admin import widgets as wagtailadmin_widgets

from networks.models import Network, NetworkContentPage


@hooks.register("register_page_listing_more_buttons")
def page_listing_more_buttons(page, page_perms, is_parent=False):
    if isinstance(page, Network):
        yield wagtailadmin_widgets.PageListingButton(
            "Convert to NetworkContentPage",
            reverse("networks:convert-network-to-content-page", kwargs={"pk": page.pk}),
            priority=10,
        )
        yield wagtailadmin_widgets.PageListingButton(
            "Convert to NetworksHome",
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
