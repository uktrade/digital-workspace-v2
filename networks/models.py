from content.models import ContentPage


class NetworksHome(ContentPage):
    is_creatable = False

    subpage_types = ["networks.Network"]


class Network(ContentPage):
    is_creatable = True

    parent_page_types = [
        "networks.NetworksHome",
        "networks.Network",
    ]
    subpage_types = ["networks.Network"]
