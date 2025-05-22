from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET

from peoplefinder.models import Person
from peoplefinder.services.team import TeamService

from .base import PeoplefinderView


class TeamSelectView(PeoplefinderView):
    def get(self, request):
        team_select_data = list(TeamService().get_team_select_data())

        return JsonResponse(team_select_data, safe=False)


@require_GET
def get_person_roles(request, person_id) -> JsonResponse:
    person = get_object_or_404(Person, id=person_id)
    person_roles_qs = person.roles.all().select_related("team")
    response = {
        "person_roles": [
            {
                "pk": person_role.pk,
                "label": f"{person_role.job_title} - {person_role.team.name}",
            }
            for person_role in person_roles_qs
        ]
    }
    return JsonResponse(response)
