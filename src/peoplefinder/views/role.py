from django.http import JsonResponse

from peoplefinder.services.team import TeamService

from .base import PeoplefinderView


class TeamSelectView(PeoplefinderView):
    def get(self, request):
        team_select_data = list(TeamService().get_team_select_data())

        return JsonResponse(team_select_data, safe=False)
