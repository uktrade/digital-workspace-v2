from django.utils.translation import gettext_lazy as _
from generic_chooser.widgets import AdminChooser

from peoplefinder.models import Network, Person, Team


class PersonChooser(AdminChooser):
    choose_one_text = _("Choose a person")
    choose_another_text = _("Choose another person")
    link_to_chosen_text = _("Edit this person")
    model = Person
    choose_modal_url_name = "person_chooser:choose"
    icon = "user"


class TeamChooser(AdminChooser):
    choose_one_text = _("Choose a team")
    choose_another_text = _("Choose another team")
    link_to_chosen_text = _("Edit this team")
    model = Team
    choose_modal_url_name = "team_chooser:choose"
    icon = "group"


class NetworkChooser(AdminChooser):
    choose_one_text = _("Choose a network")
    choose_another_text = _("Choose another network")
    link_to_chosen_text = _("Edit this network")
    model = Network
    choose_modal_url_name = "network_chooser:choose"
    icon = "globe"
