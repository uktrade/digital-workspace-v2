from wagtail.search.backends import get_search_backend

from peoplefinder.forms.search import PEOPLE_FILTER, TEAMS_FILTER
from peoplefinder.models import Person, Team


SearchResult = tuple[list[Team], list[Person]]


def search(query: str, filters: list[str]) -> SearchResult:
    s = get_search_backend()

    team_results = []
    person_results = []

    if TEAMS_FILTER in filters:
        team_results = s.search(query, Team)

    if PEOPLE_FILTER in filters:
        person_results = s.search(
            query,
            Person.objects.prefetch_related("key_skills", "additional_roles", "teams"),
        )

    return list(team_results), list(person_results)
