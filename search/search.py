import re
import unicodedata
from typing import Any, Optional

from django.db.models import QuerySet
from django.http import HttpRequest
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

    # find all properly quoted substrings with matching opening and closing "|'
    # re.split returns both matches and unmatched parts so we process everything
    matches = re.split(r"([\"'])(.*?)(\1)", query)

    output = ""
    quote_next_match = False
    valid_quotes = ['"', "'"]
    for match in matches:
        if match == "":
            continue
        if match in valid_quotes and not quote_next_match:
            quote_next_match = True  # opening quote found
            continue
        if match in valid_quotes and quote_next_match:
            quote_next_match = False  # closing quote found
            continue

        # ascii-fold all chars that can be folded
        match = unicodedata.normalize("NFKD", match)

        # replace all remaining url-unsafe chars
        cleaned_match = re.sub(r"[^a-zA-Z0-9-.~_\s]", "", match)
        if quote_next_match:
            cleaned_match = f"'{cleaned_match}'"

        output += cleaned_match

    return output
