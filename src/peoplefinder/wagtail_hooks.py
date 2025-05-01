from wagtail import hooks

from peoplefinder.views.chooser import (
    NetworkChooserViewSet,
    PersonChooserViewSet,
    TeamChooserViewSet,
)


@hooks.register("register_admin_viewset")
def register_person_chooser_viewset():
    return PersonChooserViewSet("person_chooser", url_prefix="person-chooser")


@hooks.register("register_admin_viewset")
def register_team_chooser_viewset():
    return TeamChooserViewSet("team_chooser", url_prefix="team-chooser")


@hooks.register("register_admin_viewset")
def register_network_chooser_viewset():
    return NetworkChooserViewSet("network_chooser", url_prefix="network-chooser")
