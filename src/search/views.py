import logging

from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from extended_search.models import Setting as SearchSetting
from extended_search.settings import extended_search_settings
from search.templatetags.search import SEARCH_CATEGORIES
from search.utils import get_all_subqueries

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
        {"name": k, "value": extended_search_settings[k]}
        for k in extended_search_settings.all_keys
        if "boost_parts" in k
    ]

    subqueries = get_all_subqueries(query)

    context = {
        "search_url": reverse("search:explore"),
        "search_query": query,
        "search_category": "all",
        "page": page,
        "boost_variables": boost_vars,
        "sub_queries": subqueries,
    }

    return TemplateResponse(request, "search/explore.html", context=context)
