from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET

from peoplefinder.models import Person
from peoplefinder.services.person import get_roles


@require_GET
def get_person_roles(request, person_id) -> JsonResponse:
    """
    Return the roles for a person for use in the Wagtail Admin for populating
    select inputs.
    """

    person = get_object_or_404(Person, id=person_id)
    response = {
        "person_roles": [
            {
                "pk": person_role.pk,
                "label": f"{person_role.job_title} - {person_role.team.name}",
            }
            for person_role in get_roles(person=person)
        ]
    }
    return JsonResponse(response)
