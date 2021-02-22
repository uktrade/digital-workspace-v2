from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView

from peoplefinder.models import Person
from peoplefinder.services.team import TeamService
from .base import PeoplefinderView


class ProfileDetailView(DetailView, PeoplefinderView):
    model = Person
    context_object_name = "profile"
    template_name = "peoplefinder/profile.html"

    def get_context_data(self, **kwargs: dict) -> dict:
        context = super().get_context_data(**kwargs)

        profile = context["profile"]
        roles = profile.roles.select_related("team").all()

        context["roles"] = roles

        if roles:
            # TODO: How do we know which team to select as the main one?
            team = roles[0].team
            context["team"] = team
            # TODO: `parent_teams` is common to all views. Perhaps we should
            # refactor this into a common base view or mixin?
            context["parent_teams"] = TeamService().get_all_parent_teams(team)

        return context


class ProfileEditView(UserPassesTestMixin, UpdateView, PeoplefinderView):
    model = Person
    template_name = "peoplefinder/profile-edit.html"
    fields = ["manager", "do_not_work_for_dit"]

    def test_func(self) -> bool:
        # The profile must be that of the logged in user.
        return self.get_object().user == self.request.user
