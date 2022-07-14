from django.http import HttpRequest
from wagtail.search.backends import get_search_backend
from wagtail.search.utils import parse_query_string

from peoplefinder.forms.search import PEOPLE_FILTER, TEAMS_FILTER
from peoplefinder.models import Person, Team


SearchResult = tuple[list[Team], list[Person]]


def search(request: HttpRequest, query: str, filters: list[str]) -> SearchResult:
    s = get_search_backend()

    _, query = parse_query_string(query, operator="and")

    team_results = []
    person_results = []

    if TEAMS_FILTER in filters:
        team_results = s.search(query, Team)[:50]

    if PEOPLE_FILTER in filters:
        qs = Person.objects.all()

        if not request.user.has_perm("peoplefinder.delete_person"):
            qs = qs.active()

        qs = qs.prefetch_related("key_skills", "additional_roles", "teams")

        person_results = s.search(query, qs)[:50]

    return list(team_results), list(person_results)
