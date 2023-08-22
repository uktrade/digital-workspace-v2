from django.views.generic import DetailView, TemplateView

from peoplefinder.models import Person, Team
from peoplefinder.services.person import PersonService
from peoplefinder.services.team import TeamService
from peoplefinder.views.base import PeoplefinderView


class OrganogramView(DetailView, PeoplefinderView):
    template_name = "peoplefinder/organogram.html"


class OrganogramTeamView(OrganogramView):
    model = Team
    context_object_name = "team"

    def get_context_data(self, **kwargs: dict) -> dict:
        context = super().get_context_data(**kwargs)

        team = context["team"]
        team_service = TeamService()

        context["focus"] = "team"
        context["parent_teams"] = team_service.get_all_parent_teams(team)
        context["parent_team"] = team_service.get_immediate_parent_team(team)
        context["child_teams"] = team_service.get_immediate_child_teams(team)

        return context


class OrganogramPersonView(OrganogramView):
    model = Person
    context_object_name = "profile"
    slug_url_kwarg = "profile_slug"

    def get_queryset(self):
        return super().get_queryset().active()

    def get_context_data(self, **kwargs: dict) -> dict:
        context = super().get_context_data(**kwargs)

        context["focus"] = "person"
        profile = context["profile"]
        roles = profile.roles.select_related("team").all()
        context["roles"] = roles
        context["manager"] = profile.manager
        context["manages_profiles"] = self.get_queryset().filter(manager=profile)

        if roles:
            team = roles[0].team
            context["team"] = team
            context["parent_teams"] = list(TeamService().get_all_parent_teams(team)) + [
                team
            ]

        return context
