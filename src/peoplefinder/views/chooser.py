from django.utils.translation import gettext_lazy as _
from generic_chooser.views import ChooserListingTabMixin, ModelChooserViewSet

from peoplefinder.models import Network, Person, Team


class PersonChooserListingTabMixin(ChooserListingTabMixin):
    results_template = "peoplefinder/widgets/person_chooser_results.html"


class PersonChooserViewSet(ModelChooserViewSet):
    listing_tab_mixin_class = PersonChooserListingTabMixin

    icon = "user"
    model = Person
    page_title = _("Choose a person")
    per_page = 10
    order_by = "preferred_first_name"


class TeamChooserViewSet(ModelChooserViewSet):
    icon = "globe"
    model = Team
    page_title = _("Choose a team")
    per_page = 10
    order_by = "name"


class NetworkChooserViewSet(ModelChooserViewSet):
    icon = "globe"
    model = Network
    page_title = _("Choose a network")
    per_page = 10
    order_by = "name"
