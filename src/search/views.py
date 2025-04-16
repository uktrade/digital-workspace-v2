import csv
import logging

import sentry_sdk
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from content.models import ContentPage
from extended_search.models import Setting as SearchSetting
from extended_search.settings import settings_singleton
from peoplefinder.models import Person, Team
from search.templatetags import search as search_template_tag


logger = logging.getLogger(__name__)


def can_view_explore():
    return user_passes_test(lambda u: u.has_perm("extended_search.view_explore"))


def can_export_search():
    return user_passes_test(lambda u: u.has_perm("extended_search.export_search"))


@require_http_methods(["GET"])
def autocomplete(request: HttpRequest) -> HttpResponse:
    _category = "autocomplete"
    query = request.GET.get("query", "")
    page = "1"

    search_results = search_template_tag.autocomplete(request, query)

    context = {
        "search_url": reverse("search:autocomplete"),
        "search_query": query,
        "search_category": _category,
        "search_results": list(
            search_results["pages"] + search_results["people"] + search_results["teams"]
        ),
        "pages": search_results["pages"],
        "pages_count": len(search_results["pages"]),
        "people": search_results["people"],
        "people_count": len(search_results["people"]),
        "teams": search_results["teams"],
        "teams_count": len(search_results["teams"]),
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
def search(request: HttpRequest, category: str | None = None) -> HttpResponse:
    query = request.GET.get("query", "")
    page = request.GET.get("page", "1")
    tab_override = request.GET.get("tab_override", False)

    # If the category is invalid, redirect to search all.
    if category not in search_template_tag.SEARCH_CATEGORIES:
        return redirect(
            reverse("search:category", kwargs={"category": "all"}) + f"?query={query}"
        )

    context = {
        "search_url": reverse("search:category", args=[category]),
        "search_query": query,
        "tab_override": tab_override,
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
    from search.utils import get_query_info_for_model

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
        for k in settings_singleton.all_keys()
        if "boost_parts" in k
    ]

    subqueries = {
        "pages": get_query_info_for_model(ContentPage, query),
        "people": get_query_info_for_model(Person, query),
        "teams": get_query_info_for_model(Team, query),
    }

    context = {
        "search_url": reverse("search:explore"),
        "search_query": query,
        "search_category": "all",
        "page": page,
        "boost_variables": boost_vars,
        "sub_queries": subqueries,
    }

    return TemplateResponse(request, "search/explore.html", context=context)


@can_export_search()
def export_search(request: HttpRequest, category: str) -> HttpResponse:
    """
    Administrative view for exporting search results as csv
    """
    from search.utils import SEARCH_EXPORT_MAPPINGS

    query = request.GET.get("query", "")
    if category == "all":
        search_vector = search_template_tag.SEARCH_VECTORS["all_pages"](request)
    else:
        search_vector = search_template_tag.SEARCH_VECTORS[category](request)

    search_results = search_vector.search(query)
    search_model = search_vector.model

    export_mapping = None
    for k, v in SEARCH_EXPORT_MAPPINGS.items():
        if issubclass(search_model, k):
            export_mapping = v
            break

    if not export_mapping:
        raise TypeError(
            f"'{search_model}' is not a model that is configured for export"
        )

    filename = f"search_export_{category}.csv"
    response = HttpResponse(
        content_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

    writer = csv.writer(response)
    writer.writerow(export_mapping["header"])

    for result in search_results:
        row = export_mapping["item_to_row_function"](result, request)
        writer.writerow(row)

    return response
