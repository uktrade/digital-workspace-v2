from wagtail import hooks

from peoplefinder.views.chooser import (
    person_chooser_viewset,
    team_chooser_viewset,
)


@hooks.register("register_admin_viewset")
def register_person_chooser_viewset():
    return person_chooser_viewset


@hooks.register("register_admin_viewset")
def register_team_chooser_viewset():
    return team_chooser_viewset
