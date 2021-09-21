from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import SuspiciousOperation
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Avg, Q, QuerySet
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from peoplefinder.forms.team import TeamForm
from peoplefinder.models import Person, Team, TeamMember
from peoplefinder.services.audit_log import AuditLogService
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

        if self.request.user.has_perm("peoplefinder.delete_team"):
            (
                context["can_team_be_deleted"],
                context["reasons_team_cannot_be_deleted"],
            ) = team_service.can_team_be_deleted(team)

        # Must be a leaf team.
        if not context["sub_teams"]:
            context["members"] = team.members.all()
        else:
            context["people_outside_subteams_count"] = TeamMember.objects.filter(
                team=team
            ).count()

            # Warning: Multiple requests per sub-team. This might need optimising in the
            # future.
            for sub_team in context["sub_teams"]:
                sub_team.avg_profile_completion = (
                    Person.objects.with_profile_completion()
                    .filter(
                        teams__in=[
                            sub_team,
                            *team_service.get_all_child_teams(sub_team),
                        ]
                    )
                    .aggregate(Avg("profile_completion"))["profile_completion__avg"]
                )

        if self.request.user.has_perm("peoplefinder.view_audit_log"):
            context["team_audit_log"] = AuditLogService.get_audit_log(team)

        return context


@method_decorator(transaction.atomic, name="post")
class TeamEditView(PermissionRequiredMixin, UpdateView, PeoplefinderView):
    model = Team
    context_object_name = "team"
    form_class = TeamForm
    template_name = "peoplefinder/team-edit.html"
    permission_required = "peoplefinder.change_team"

    def get_context_data(self, **kwargs: dict) -> dict:
        context = super().get_context_data(**kwargs)

        team = context["team"]
        team_service = TeamService()

        context["parent_team"] = team_service.get_immediate_parent_team(team)
        context["is_root_team"] = team_service.get_root_team() == team

        return context

    def form_valid(self, form):
        response = super().form_valid(form)

        if form.has_changed():
            TeamService().team_updated(self.object, self.request.user)

        return response


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
        paginator = Paginator(members, 40)
        context["team_members"] = paginator.page(page)
        context["page_numbers"] = list(paginator.get_elided_page_range(page))

        context["heading"] = self.heading

        return context


class TeamPeopleView(TeamPeopleBaseView):
    heading = "All people"

    def get_team_members(self, team: Team, sub_teams: QuerySet) -> QuerySet:
        return TeamMember.objects.filter(Q(team=team) | Q(team__in=sub_teams)).order_by(
            "person__first_name", "person__last_name"
        )


class TeamPeopleOutsideSubteamsView(TeamPeopleBaseView):
    heading = "People not in a sub-team"

    def get_team_members(self, team: Team, sub_teams: QuerySet) -> QuerySet:
        return TeamMember.objects.filter(team=team).order_by(
            "person__first_name", "person__last_name"
        )


@method_decorator(transaction.atomic, name="post")
class TeamAddNewSubteamView(PermissionRequiredMixin, CreateView, PeoplefinderView):
    model = Team
    form_class = TeamForm
    template_name = "peoplefinder/team-add-new-subteam.html"
    permission_required = "peoplefinder.add_team"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        self.parent_team = Team.objects.get(slug=self.kwargs["slug"])

    def get_initial(self):
        return {"parent_team": self.parent_team}

    def get_context_data(self, **kwargs: dict) -> dict:
        context = super().get_context_data(**kwargs)

        context["parent_team"] = self.parent_team
        context["is_root_team"] = False

        return context

    def form_valid(self, form):
        response = super().form_valid(form)

        TeamService().team_created(self.object, self.request.user)

        return response


@method_decorator(transaction.atomic, name="delete")
class TeamDeleteView(PermissionRequiredMixin, DeleteView, PeoplefinderView):
    model = Team
    context_object_name = "team"
    success_url = reverse_lazy("team-home")
    template_name = "peoplefinder/team-confirm-delete.html"
    permission_required = "peoplefinder.delete_team"

    def get_context_data(self, **kwargs: dict) -> dict:
        context = super().get_context_data(**kwargs)

        (
            context["can_team_be_deleted"],
            context["reasons_team_cannot_be_deleted"],
        ) = TeamService().can_team_be_deleted(context["team"])

        return context

    def delete(self, request, *args, **kwargs):
        team = self.get_object()

        can_team_be_deleted, _ = TeamService().can_team_be_deleted(team)

        if not can_team_be_deleted:
            raise SuspiciousOperation("Team cannot be deleted")

        TeamService().team_deleted(team, self.request.user)

        return super().delete(request, *args, **kwargs)
