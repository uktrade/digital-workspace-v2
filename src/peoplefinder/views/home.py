from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, reverse

from core.utils import flag_is_active
from core import flags
from peoplefinder.services.team import TeamService

from .base import PeoplefinderView


class PeopleHome(PeoplefinderView):
    def get(self, request: HttpRequest) -> HttpResponse:
        if flag_is_active(request, flag_name=flags.PF_DISCOVER):
            return redirect(
                reverse("people-discover")
            )
        return redirect(
            reverse("profile-view", kwargs={"profile_slug": request.user.profile.slug})
        )


class TeamHome(PeoplefinderView):
    def get(self, request: HttpRequest) -> HttpResponse:
        root_team = TeamService().get_root_team()

        return redirect(reverse("team-view", kwargs={"slug": root_team.slug}))
