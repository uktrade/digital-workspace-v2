import logging

import sentry_sdk
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from wagtail.search.query import Fuzzy, Or, Phrase, PlainText

from content.models import ContentPage, ContentPageIndexManager
from extended_search.backends.query import OnlyFields
from extended_search.models import Setting as SearchSetting
from extended_search.settings import extended_search_settings
from peoplefinder.models import Person, PersonIndexManager, Team, TeamIndexManager
from search.templatetags import search as search_template_tag

logger = logging.getLogger(__name__)


def can_view_explore():
    return user_passes_test(lambda u: u.has_perm("extended_search.view_explore"))


@require_http_methods(["GET"])
def autocomplete(request: HttpRequest) -> HttpResponse:
    _category = "autocomplete"
    query = request.GET.get("query", "")
    page = "1"

    search_results = search_template_tag.autocomplete(request, query)

    print(search_results["tools"])

    context = {
        "search_url": reverse("search:autocomplete"),
        "search_query": query,
        "search_category": _category,
        "search_results": list(
            search_results["pages"]
            + search_results["people"]
            + search_results["teams"]
            + search_results["tools"]
        ),
        "pages": search_results["pages"],
        "people": search_results["people"],
        "teams": search_results["teams"],
        "tools": search_results["tools"],
        "page": page,
        "search_feedback_initial": {
            "search_query": query,
            "search_data": {"category": _category},
        },
    }

    return TemplateResponse(
        request, "search/partials/result/autocomplete_page.html", context=context
    )


@require_http_methods(["GET"])
def search(request: HttpRequest, category: str = None) -> HttpResponse:
    query = request.GET.get("query", "")
    page = request.GET.get("page", "1")

    # If the category is invalid, redirect to search all.
    if category not in search_template_tag.SEARCH_CATEGORIES:
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

    # https://docs.sentry.io/platforms/python/performance/instrumentation/custom-instrumentation/#accessing-the-current-transaction
    transaction = sentry_sdk.Hub.current.scope.transaction

    if transaction is not None:
        transaction.set_tag("search.category", category)
        transaction.set_tag("search.query", query)
        transaction.set_tag("search.page", page)

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
        {"name": k, "value": extended_search_settings[k]}
        for k in extended_search_settings.all_keys
        if "boost_parts" in k
    ]

    subqueries = {"pages": [], "people": [], "teams": []}
    analyzer_field_suffices = [
        (k, v["index_fieldname_suffix"])
        for k, v in extended_search_settings["analyzers"].items()
    ]
    for mapping in ContentPageIndexManager.get_mapping():
        field = ContentPageIndexManager._get_search_query_from_mapping(
            query, ContentPage, mapping
        )
        get_query_info(subqueries["pages"], field, mapping, analyzer_field_suffices)
    for mapping in PersonIndexManager.get_mapping():
        field = PersonIndexManager._get_search_query_from_mapping(
            query, Person, mapping
        )
        get_query_info(subqueries["people"], field, mapping, analyzer_field_suffices)
    for mapping in TeamIndexManager.get_mapping():
        field = TeamIndexManager._get_search_query_from_mapping(query, Team, mapping)
        get_query_info(subqueries["teams"], field, mapping, analyzer_field_suffices)

    context = {
        "search_url": reverse("search:explore"),
        "search_query": query,
        "search_category": "all",
        "page": page,
        "boost_variables": boost_vars,
        "sub_queries": subqueries,
    }

    return TemplateResponse(request, "search/explore.html", context=context)


def get_query_info(fields, field, mapping, suffix_map):
    if field is None:
        return fields

    if isinstance(field, Or):
        for f in field.subqueries:
            fields = get_query_info(fields, f, mapping, suffix_map)

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
                "field": mapping["model_field_name"],
                "analyzer": analyzer_name,
                "boost": field.subquery.boost,
            }
        )
    return fields
