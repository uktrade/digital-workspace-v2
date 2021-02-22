from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, reverse

from peoplefinder.services.team import TeamService
from .base import PeoplefinderView


class PeopleHome(PeoplefinderView):
    def get(self, request: HttpRequest) -> HttpResponse:
        return redirect(reverse("profile-view", kwargs={"pk": request.user.id}))


class TeamHome(PeoplefinderView):
    def get(self, request: HttpRequest) -> HttpResponse:
        root_team = TeamService().get_root_team()

        return redirect(reverse("team-view", kwargs={"slug": root_team.slug}))
