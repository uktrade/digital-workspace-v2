from typing import Any, Optional
import unicodedata

from django.db.models import QuerySet
from django.http import HttpRequest
import re
from wagtail.search.backends import get_search_backend
from wagtail.search.utils import parse_query_string

from content.models import ContentPage
from peoplefinder.models import Person, Team

from .forms import SearchCategory


def search_all(
    request: HttpRequest, query: str, category: Optional[SearchCategory]
) -> tuple[list[Any], list[Any], list[Any]]:
    s = get_search_backend()

    _, query = parse_query_string(query, operator="and")

    page_results = []
    people_results = []
    team_results = []

    if category in (SearchCategory.PAGES, None):
        page_results += s.search(query, _content_page_query(request))

    if category in (SearchCategory.TEAMS, None):
        team_results += s.search(query, _team_query(request))

    if category in (SearchCategory.PEOPLE, None):
        people_results += s.search(query, _person_query(request))

    return page_results, team_results, people_results


def _content_page_query(request: HttpRequest) -> QuerySet:
    return ContentPage.objects.public().live()


def _person_query(request: HttpRequest) -> QuerySet:
    people = Person.objects.all()

    if not request.user.has_perm("peoplefinder.delete_person"):
        people.active()

    people.prefetch_related("key_skills", "additional_roles", "teams")

    return people


def _team_query(request: HttpRequest) -> QuerySet:
    return Team.objects.all()


def sanitize_search_query(query: Optional[str] = None) -> str:
    if query is None:
        return ""

    output = re.sub('[^a-zA-Z0-9-.~_\s]', "", query)
    if not unicodedata.is_normalized("NFKD", output):
        output = unicodedata.normalize("NFKD", output)

    return output
