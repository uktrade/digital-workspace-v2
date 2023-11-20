import logging

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from wagtail.search.query import Fuzzy, Or, Phrase, PlainText

from content.models import ContentPage
from extended_search.backends.query import OnlyFields
from extended_search.managers.query_builder import CustomQueryBuilder
from extended_search.models import Setting as SearchSetting
from extended_search.settings import settings_singleton
from peoplefinder.models import Person, Team
from search.templatetags.search import SEARCH_CATEGORIES

logger = logging.getLogger(__name__)


def can_view_explore():
    return user_passes_test(lambda u: u.has_perm("extended_search.view_explore"))


@require_http_methods(["GET"])
def search(request: HttpRequest, category: str = None) -> HttpResponse:
    query = request.GET.get("query", "")
    page = request.GET.get("page", "1")

    # If the category is invalid, redirect to search all.
    if category not in SEARCH_CATEGORIES:
        return redirect(
            reverse("search:category", kwargs={"category": "all"}) + f"?query={query}"
        )

    context = {
        "search_url": reverse("search:category", args=[category]),
        "search_query": query,
        "search_category": category,
        "page": page,
        "search_feedback_initial": {
            "search_query": query,
            "search_data": {"category": category},
        },
    }

    return TemplateResponse(request, "search/search.html", context=context)


@can_view_explore()
def explore(request: HttpRequest) -> HttpResponse:
    """
    Administrative view for exploring search options, boosts, etc
    """
    if request.method == "POST":
        if not request.user.has_perm("extended_search.change_setting"):
            messages.error(request, "You are not authorised to edit settings")

        key = request.POST.get("key")
        value = request.POST.get("value")

        SearchSetting.objects.update_or_create(key=key, defaults={"value": value})
        messages.info(request, f"Setting '{key}' saved")

    query = request.GET.get("query", "")
    page = request.GET.get("page", "1")

    boost_vars = [
        {"name": k, "value": settings_singleton[k]}
        for k in settings_singleton.all_keys
        if "boost_parts" in k
    ]

    subqueries = {"pages": [], "people": [], "teams": []}
    analyzer_field_suffices = [
        (k, v["index_fieldname_suffix"])
        for k, v in settings_singleton["analyzers"].items()
    ]
    for index_field in ContentPage.indexed_fields:
        field = CustomQueryBuilder._build_search_query(query, ContentPage, index_field)
        get_query_info(subqueries["pages"], field, index_field, analyzer_field_suffices)
    for index_field in Person.indexed_fields:
        field = CustomQueryBuilder._build_search_query(query, Person, index_field)
        get_query_info(
            subqueries["people"], field, index_field, analyzer_field_suffices
        )
    for index_field in Team.indexed_fields:
        field = CustomQueryBuilder._build_search_query(query, Team, index_field)
        get_query_info(subqueries["teams"], field, index_field, analyzer_field_suffices)

    context = {
        "search_url": reverse("search:explore"),
        "search_query": query,
        "search_category": "all",
        "page": page,
        "boost_variables": boost_vars,
        "sub_queries": subqueries,
    }

    return TemplateResponse(request, "search/explore.html", context=context)


def get_query_info(fields, field, index_field, suffix_map):
    if field is None:
        return fields

    if isinstance(field, Or):
        for f in field.subqueries:
            fields = get_query_info(fields, f, index_field, suffix_map)

    elif isinstance(field, OnlyFields):
        core_field = field.subquery.subquery

        analyzer_name = "tokenizer"
        for analyzer, suffix in suffix_map:
            if suffix and suffix in field.fields[0]:
                analyzer_name = analyzer

        if isinstance(core_field, Phrase):
            query_type = "phrase"
        elif isinstance(core_field, Fuzzy):
            query_type = "fuzzy"
        elif isinstance(core_field, PlainText):
            if core_field.operator == "and":
                query_type = "query_and"
            else:
                query_type = "query_or"
        fields.append(
            {
                "query_type": query_type,
                "field": index_field.model_field_name,
                "analyzer": analyzer_name,
                "boost": field.subquery.boost,
            }
        )
    return fields
