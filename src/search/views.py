import logging
from django.contrib.auth.decorators import user_passes_test
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from search.templatetags.search import SEARCH_CATEGORIES
from search_extended.settings import search_extended_settings


logger = logging.getLogger(__name__)


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
    }

    return TemplateResponse(request, "search/search.html", context=context)


def can_explore_search():
    allowed_user_emails = [
        "marcel.kornblum@digital.trade.gov.uk",
        "samuel.dudley@digital.trade.gov.uk",
        "cameron.lamb@digital.trade.gov.uk",
        "luisella.strona@trade.gov.uk",
        "kristina.iankova@trade.gov.uk",
        "sajid.arif@trade.gov.uk",
        "alfie.dennen@trade.gov.uk",
        "jonathan.anderson2@trade.gov.uk",
        "elizabeth.ferguson@trade.gov.uk",
        "naomi.cauchi@trade.gov.uk",
        "jamil.ahmed@trade.gov.uk",
        "aleesha.hussain@trade.gov.uk",
        "ross.miller@digital.trade.gov.uk",
    ]
    return user_passes_test(lambda u: u.email in allowed_user_emails)


@can_explore_search()
def explore(request: HttpRequest) -> HttpResponse:
    """
    Administrative view for exploring search options, boosts, etc
    """
    query = request.GET.get("query", "")
    page = request.GET.get("page", "1")

    boost_vars = [{"name": f"SEARCH_BOOST_{k}", "value": v} for k, v in search_extended_settings.BOOST_VARIABLES.items()]

    context = {
        "search_url": reverse("search:explore"),
        "search_query": query,
        "search_category": "all",
        "page": page,
        "boost_variables": boost_vars,
        "sub_queries": [
            {
                "name": "pages",
                "queries": [{"id": 1, "value": "{match_all: {}}"}]
            },
            {
                "name": "people",
                "queries": [{"id": 1, "value": "{match_all: {}}"}]
            },
            {
                "name": "teams",
                "queries": [{"id": 1, "value": "{match_all: {}}"}]
            },
        ],
    }

    return TemplateResponse(request, "search/explore.html", context=context)
