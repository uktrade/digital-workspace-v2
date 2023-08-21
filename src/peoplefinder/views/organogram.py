from django.views.generic import DetailView, TemplateView

from peoplefinder.models import Person, Team
from peoplefinder.services.person import PersonService
from peoplefinder.services.team import TeamService
from peoplefinder.views.base import PeoplefinderView


# class OrganogramPersonView(TemplateView):
#     template_name = "peoplefinder/organogram.html"


# class OrganogramTeamView(TemplateView):
#     template_name = "peoplefinder/organogram.html"

#     def get(self, slug=None):
#         ...


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

        profile = context["profile"]
        roles = profile.roles.select_related("team").all()

        context["focus"] = "person"
        context["roles"] = roles
        context["title"] = profile.full_name

        if roles:
            # TODO: How do we know which team to select as the main one?
            team = roles[0].team
            context["team"] = team
            # TODO: `parent_teams` is common to all views. Perhaps we should
            # refactor this into a common base view or mixin?
            context["parent_teams"] = list(TeamService().get_all_parent_teams(team)) + [
                team
            ]

        return context
