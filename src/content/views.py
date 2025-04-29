from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET

from peoplefinder.models import Person


@require_GET
def get_user_roles(request, person_id) -> JsonResponse:
    person = get_object_or_404(Person, id=person_id)
    person_roles_qs = person.roles.all().select_related("team")
    response = {
        "person_roles": [
            f"{person_role.job_title},{person_role.team.name}"
            for person_role in person_roles_qs
        ]
    }
    return JsonResponse(response)
