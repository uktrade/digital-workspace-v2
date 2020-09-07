from content.models import DirectChildrenMixin

from content.models import ContentPage


class NetworksHome(DirectChildrenMixin, ContentPage):
    is_creatable = False

    subpage_types = ["networks.Network"]


class Network(DirectChildrenMixin, ContentPage):
    is_creatable = True

    parent_page_types = ['networks.NetworksHome', "networks.Network",]
    subpage_types = ["networks.Network"]
