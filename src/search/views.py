import logging
import math
import shlex
from functools import wraps

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from search.templatetags.search import SEARCH_CATEGORIES


logger = logging.getLogger(__name__)


# Views
@require_http_methods(["GET"])
def home_view(request: HttpRequest) -> HttpResponse:
    query = request.GET.get("query", "")
    return redirect(
        reverse("search:category", kwargs={"category": "all"}) + f"?query={query}"
    )


@require_http_methods(["GET"])
def search_v2(request: HttpRequest, category: str) -> HttpResponse:
    query = request.GET.get("query", "")
    page = request.GET.get("page", "1")

    # If the category is invalid, redirect to search all.
    if category not in SEARCH_CATEGORIES:
        return redirect(reverse("search:home") + f"?query={query}")

    context = {
        "search_url": reverse("search:category", args=[category]),
        "search_query": query,
        "search_category": category,
        "page": page,
    }

    return TemplateResponse(request, "search/search_v2.html", context=context)
