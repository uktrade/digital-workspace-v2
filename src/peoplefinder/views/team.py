from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import SuspiciousOperation
from django.db import models, transaction
from django.db.models import QuerySet
from django.http import HttpRequest
from django.http.response import HttpResponse as HttpResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from peoplefinder.forms.team import TeamForm
from peoplefinder.models import Team, TeamMember
from peoplefinder.services.audit_log import AuditLogService
from peoplefinder.services.team import TeamService

from .base import PeoplefinderView


# TODO: Potential to refactor for the common parts.


class TeamDetailView(DetailView, PeoplefinderView):
    model = Team
    context_object_name = "team"
    template_name = "peoplefinder/team.html"

    class SubView(models.TextChoices):
        SUB_TEAMS = "sub-teams", "Teams"
        PEOPLE = "people", "People"

    def setup(self, request: HttpRequest, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        sub_view_str = self.request.GET.get("sub_view", None)
        self.sub_view = None
        if sub_view_str:
            self.sub_view = self.SubView(sub_view_str)

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        response = super().dispatch(request, *args, **kwargs)
        if self.sub_view is None:
            sub_view = self.SubView.PEOPLE
            if self.available_sub_views:
                sub_view = self.available_sub_views[0]

            team_detail_path = reverse("team-view", args=[self.object.slug])
            return redirect(f"{team_detail_path}?sub_view={sub_view}")
        return response

    @cached_property
    def parent_teams(self) -> QuerySet[Team]:
        return TeamService().get_all_parent_teams(self.object)

    @cached_property
    def sub_teams(self) -> list[Team]:
        sub_teams = []

        team_service = TeamService()
        for sub_team in team_service.get_immediate_child_teams(self.object):
            profile_completion = team_service.profile_completion(sub_team)
            if profile_completion:
                profile_completion_percentage = round(
                    float(profile_completion * 100), 2
                )
                sub_team.profile_completion = (
                    f"{profile_completion_percentage:g}% of profiles complete"
                )
            sub_teams.append(sub_team)

        return sub_teams

    @cached_property
    def leaders(self) -> list[TeamMember]:
        return list(self.object.leaders)

    @cached_property
    def members(self) -> list[TeamMember]:
        return (
            self.object.members.all()
            .active()
            .exclude(id__in=[leader.id for leader in self.leaders])
            .select_related(
                "person",
                "person__uk_office_location",
            )
            .order_by("person__first_name", "person__last_name")
            .distinct("person", "person__first_name", "person__last_name")
        )

    @cached_property
    def available_sub_views(self) -> list["TeamDetailView.SubView"]:
        available_sub_views = []
        if self.sub_teams:
            available_sub_views.append(self.SubView.SUB_TEAMS)
        if self.members:
            available_sub_views.append(self.SubView.PEOPLE)
        return available_sub_views

    def get_context_data(self, **kwargs: dict) -> dict:
        context = super().get_context_data(**kwargs)

        context.update(
            page_title=self.object.name,
            team_breadcrumbs=True,
            parent_teams=self.parent_teams,
            sub_teams=self.sub_teams,
            current_sub_view=self.sub_view,
            sub_views=self.available_sub_views,
            teams_active=self.sub_view == self.SubView.SUB_TEAMS,
            leaders=self.leaders,
            members=self.members,
        )

        team_service = TeamService()

        if profile_completion := team_service.profile_completion(self.object):
            profile_completion_percentage = round(float(profile_completion * 100), 2)
            context["profile_completion"] = (
                f"{profile_completion_percentage:g}% of profiles complete"
            )

        if self.request.user.has_perm("peoplefinder.delete_team"):
            (
                context["can_team_be_deleted"],
                context["reasons_team_cannot_be_deleted"],
            ) = team_service.can_team_be_deleted(self.object)

        if self.request.user.has_perms(
            ["peoplefinder.change_team", "peoplefinder.view_auditlog"]
        ):
            context["team_audit_log"] = AuditLogService.get_audit_log(self.object)

        return context


@method_decorator(transaction.atomic, name="post")
class TeamEditView(PermissionRequiredMixin, UpdateView, PeoplefinderView):
    model = Team
    context_object_name = "team"
    form_class = TeamForm
    template_name = "peoplefinder/team-edit.html"
    permission_required = "peoplefinder.change_team"

    def get_initial(self):
        leaders_positions = None

        if leaders := list(self.object.leaders):
            leaders_positions = ",".join([str(member.pk) for member in leaders])

        return {"leaders_positions": leaders_positions}

    def get_context_data(self, **kwargs: dict) -> dict:
        context = super().get_context_data(**kwargs)

        team = self.object
        team_service = TeamService()
        page_title = f"Edit {team.name}"

        context.update(
            page_title=page_title,
            team_breadcrumbs=True,
            extra_breadcrumbs=[(None, page_title)],
            parent_team=team_service.get_immediate_parent_team(team),
            is_root_team=team_service.get_root_team() == team,
            team_leaders_order_component={
                "ordering": team.leaders_ordering,
                "members": [
                    {"pk": member.pk, "name": member.person.full_name}
                    for member in team.leaders
                ],
            },
        )

        return context

    def form_valid(self, form):
        response = super().form_valid(form)

        # Update the order of the team leaders.
        if (
            self.object.leaders_ordering == Team.LeadersOrdering.ALPHABETICAL
            or not form.cleaned_data["leaders_positions"]
        ):
            for member in self.object.members.all().active():
                member.leaders_position = None
                member.save()
        elif self.object.leaders_ordering == Team.LeadersOrdering.CUSTOM:
            for i, member_pk in enumerate(form.cleaned_data["leaders_positions"]):
                member = TeamMember.active.get(pk=member_pk)
                member.leaders_position = i
                member.save()

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
        page_title = f"All sub-teams ({team.short_name})"

        context.update(
            parent_teams=team_service.get_all_parent_teams(team),
            team_breadcrumbs=True,
            extra_breadcrumbs=[(None, page_title)],
            page_title=page_title,
        )

        return context


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
        return {"parent_team": self.parent_team.pk}

    def get_context_data(self, **kwargs: dict) -> dict:
        context = super().get_context_data(**kwargs)
        page_title = "Add new sub-team"

        context.update(
            page_title=page_title,
            team_breadcrumbs=True,
            extra_breadcrumbs=[(None, page_title)],
            parent_team=self.parent_team,
            is_root_team=False,
        )

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
