from django.utils.translation import gettext_lazy as _
from wagtail.admin.views.generic import chooser as chooser_views
from wagtail.admin.viewsets.chooser import ChooserViewSet

from peoplefinder.models import Person, Team


class PersonBaseChooseView(chooser_views.BaseChooseView):
    ordering = ["preferred_first_name"]


class PersonChooseView(chooser_views.ChooseView, PersonBaseChooseView): ...


class PersonChooseResultsView(
    chooser_views.ChooseResultsView, PersonBaseChooseView
): ...


class PersonChooserViewSet(ChooserViewSet):
    choose_view_class = PersonChooseView
    choose_results_view_class = PersonChooseResultsView

    icon = "user"
    model = Person
    per_page = 10
    page_title = _("Choose a person")
    choose_one_text = _("Choose a person")
    choose_another_text = _("Choose another person")
    link_to_chosen_text = _("Edit this person")


person_chooser_viewset = PersonChooserViewSet("person_chooser")


class TeamBaseChooseView(chooser_views.BaseChooseView):
    ordering = ["name"]


class TeamChooseView(chooser_views.ChooseView, TeamBaseChooseView): ...


class TeamChooseResultsView(chooser_views.ChooseResultsView, TeamBaseChooseView): ...


class TeamChooserViewSet(ChooserViewSet):
    choose_view_class = TeamChooseView
    choose_results_view_class = TeamChooseResultsView

    icon = "group"
    model = Team
    per_page = 10
    page_title = _("Choose a team")
    choose_one_text = _("Choose a team")
    choose_another_text = _("Choose another team")
    link_to_chosen_text = _("Edit this team")


team_chooser_viewset = TeamChooserViewSet("team_chooser")
