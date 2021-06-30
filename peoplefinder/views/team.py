from django.core.paginator import Paginator
from django.db.models import Q, QuerySet
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView

from peoplefinder.forms.team import TeamForm
from peoplefinder.models import Team, TeamMember
from peoplefinder.services.team import TeamService
from .base import PeoplefinderView


# TODO: Potential to refactor for the common parts.


class TeamDetailView(DetailView, PeoplefinderView):
    model = Team
    context_object_name = "team"
    template_name = "peoplefinder/team.html"

    def get_context_data(self, **kwargs: dict) -> dict:
        context = super().get_context_data(**kwargs)

        team = context["team"]
        team_service = TeamService()

        context["parent_teams"] = team_service.get_all_parent_teams(team)
        context["sub_teams"] = team_service.get_immediate_child_teams(team)

        # Must be a leaf team.
        if not context["sub_teams"]:
            context["members"] = team.members.all()
        else:
            context["people_outside_subteams_count"] = TeamMember.objects.filter(
                team=team
            ).count()

        return context


class TeamEditView(UpdateView, PeoplefinderView):
    model = Team
    context_object_name = "team"
    form_class = TeamForm
    template_name = "peoplefinder/team-edit.html"

    def get_context_data(self, **kwargs: dict) -> dict:
        context = super().get_context_data(**kwargs)

        team = context["team"]
        team_service = TeamService()

        context["parent_team"] = team_service.get_immediate_parent_team(team)
        context["is_root_team"] = team_service.get_root_team() == team

        return context


class TeamTreeView(DetailView, PeoplefinderView):
    model = Team
    context_object_name = "team"
    template_name = "peoplefinder/team-tree.html"

    def get_context_data(self, **kwargs: dict) -> dict:
        context = super().get_context_data(**kwargs)

        team = context["team"]
        team_service = TeamService()

        context["parent_teams"] = team_service.get_all_parent_teams(team)

        return context


class TeamPeopleBaseView(DetailView, PeoplefinderView):
    """A base view for people in a team.

    Below is a list of attributes that subclasses need to provide.

    Attributes:
        heading ([str]): Page heading
    """

    model = Team
    context_object_name = "team"
    template_name = "peoplefinder/team-people.html"

    # override in subclass
    heading = ""

    def get_team_members(self, team: Team, sub_teams: QuerySet) -> QuerySet:
        """Return the related team members.

        Subclasses must implement this method and return a queryset of team
        members. The team members will be available at "team_members" in the
        view's context data.

        Args:
            team (Team): The given current team
            sub_teams (QuerySet[Team]): The sub teams of the current team

        Return:
            (QuerySet[TeamMember]): A queryset of team members
        """
        raise NotImplementedError

    def get_context_data(self, **kwargs: dict) -> dict:
        context = super().get_context_data(**kwargs)

        page = self.request.GET.get("page", 1)

        team = context["team"]
        team_service = TeamService()

        context["parent_teams"] = team_service.get_all_parent_teams(team)
        context["sub_teams"] = team_service.get_all_child_teams(team)

        members = self.get_team_members(team, context["sub_teams"])
        context["team_members"] = Paginator(members, 40).page(page)

        context["heading"] = self.heading

        return context


class TeamPeopleView(TeamPeopleBaseView):
    heading = "All people"

    def get_team_members(self, team: Team, sub_teams: QuerySet) -> QuerySet:
        return TeamMember.objects.filter(Q(team=team) | Q(team__in=sub_teams)).order_by(
            "pk"
        )


class TeamPeopleOutsideSubteamsView(TeamPeopleBaseView):
    heading = "People not in a sub-team"

    def get_team_members(self, team: Team, sub_teams: QuerySet) -> QuerySet:
        return TeamMember.objects.filter(team=team).order_by("pk")
