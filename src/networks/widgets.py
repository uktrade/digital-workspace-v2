from django.utils.translation import gettext_lazy as _
from generic_chooser.widgets import AdminChooser


class NetworkChooser(AdminChooser):
    choose_one_text = _("Choose a network")
    choose_another_text = _("Choose another network")
    link_to_chosen_text = _("Edit this network")
    model = "networks.Network"
    choose_modal_url_name = "network_chooser:choose"
    icon = "globe"
