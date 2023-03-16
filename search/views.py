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
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

from content.models import ContentPage, SearchExclusionPageLookUp, SearchPinPageLookUp
from search.templatetags.search import SEARCH_CATEGORIES

from .utils import sanitize_search_query


logger = logging.getLogger(__name__)


# TODO[DWPF-454] remove this view
def search(request):
    page = int(request.GET.get("page", 1))
    search_query = request.GET.get("query", None)

    # users in the beta need to use the v2 search
    if request.user.enable_v2_search:
        return redirect(reverse("search:all") + f"?query={search_query}")

    if search_query is None:
        search_query = request.GET.get("s", None)

    previous_page = None
    next_page = None
    total_shown = 10

    # OR based search apart from anything quoted
    sanitized_search_query = sanitize_search_query(search_query)

    query_parts = shlex.split(sanitized_search_query.lower())
    search_terms = ""

    for query_part in query_parts:
        # Check for phrases
        if " " in query_part:
            query_part = f'"{query_part}"'

        if search_terms == "":
            search_terms = query_part
        else:
            search_terms = f"{search_terms} OR {query_part}"

    exclusions = list(
        SearchExclusionPageLookUp.objects.filter(
            search_keyword_or_phrase__keyword_or_phrase__in=query_parts,
        ).values_list(
            "object_id",
            flat=True,
        )
    )

    pinned_ids = list(
        SearchPinPageLookUp.objects.filter(
            search_keyword_or_phrase__keyword_or_phrase__in=query_parts,
        ).values_list(
            "object_id",
            flat=True,
        )
    )

    pinned_results = (
        ContentPage.objects.live()
        .filter(
            pk__in=pinned_ids,
            live=True,
        )
        .order_by(
            "-last_published_at",
        )
    )

    total = 0
    hits = []
    pagination_range = None
    show_total = pinned_results.count() + total

    if search_query:
        make_search = (
            Search(index="wagtail__wagtailcore_page")
            .using(
                Elasticsearch(
                    settings.OPENSEARCH_URL,
                )
            )
            .query(
                "query_string",
                query=search_terms,
                fields=[
                    "content_contentpage__search_title",
                    "content_contentpage__body_no_html",
                ]
                # default_field="title",
            )
            .filter(
                "term",
                live_filter=True,
            )
            .highlight(
                "search_title",
                "content_contentpage__body_no_html",
                fragment_size=150,
            )
        )

        for exclude in exclusions:
            make_search = make_search.exclude("match", pk=exclude)

        for pinned_id in pinned_ids:
            make_search = make_search.exclude("match", pk=pinned_id)

        logger.debug(f"Search dict: {make_search.to_dict()}")

        search_start = (page - 1) * total_shown

        results_start = search_start
        results_end = results_start + total_shown

        response = make_search[results_start:results_end].execute()

        total = response.hits.total.value

        hits = []

        for hit in response.hits:
            # TODO check which index the term was found in, if it's only title, no preview?
            if hit.pk not in exclusions:
                hits.append(hit)

        show_total = pinned_results.count() + total

        num_pages = math.floor(total / total_shown)

        if total % total_shown:
            num_pages += 1

        if num_pages > 1:
            start = 1

            if num_pages < total_shown:
                total_shown = num_pages

            if page > 9:
                start = page - 7
                total_shown = 10

                if (page + 2) > num_pages:
                    start = num_pages - 9

            pagination_range = range(start, (start + total_shown))

            if page < num_pages:
                next_page = page + 1

            if page > 1:
                previous_page = page - 1

    return TemplateResponse(
        request,
        "search/search.html",
        {
            "pinned_results": pinned_results,
            "num_pinned_results": pinned_results.count() if page == 1 else 0,
            "num_results": pinned_results.count() + total,
            "search_query": search_query,
            "search_results": hits,
            "pagination_range": pagination_range,
            "page": page,
            "next_page": next_page,
            "previous_page": previous_page,
            "show_total": show_total,
        },
    )


def search_view(func):
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        query = request.GET.get("query", "")

        # Users not in the beta need to use the v1 search.
        # TODO[DWPF-454] remove this
        if not request.user.enable_v2_search:
            return redirect(reverse("search") + f"?query={query}")

        return func(request, *args, **kwargs)

    return wrapper


# Views
@require_http_methods(["GET"])
@search_view
def home_view(request: HttpRequest) -> HttpResponse:
    return redirect("search:all")


@require_http_methods(["GET"])
@search_view
def search_v2(request: HttpRequest, category: str) -> HttpResponse:
    query = request.GET.get("query", "")
    page = request.GET.get("page", "1")

    # If the category is invalid, redirect to search all.
    if category not in SEARCH_CATEGORIES:
        return redirect(reverse("search:all") + f"?query={query}")

    context = {
        "search_url": reverse("search:category", args=[category]),
        "search_query": query,
        "search_category": category,
        "page": page,
    }

    return TemplateResponse(request, "search/search_v2.html", context=context)


def toggle_search_v2(request: HttpRequest, use_v2: str) -> HttpResponse:
    """
    Temporary view to allow users to opt-in or -out of the beta/V2 functionality.
    TODO [DWPF-454] Remove once Beta period is over
    """

    next = request.GET.get("next", None)
    if next is None:
        next = request.META.get("HTTP_REFERER", "/")

    if use_v2 not in [
        "on",
        "off",
    ]:
        return redirect(next)  # @TODO raise an error instead?

    user = request.user
    use_v2 = True if use_v2 == "on" else False
    if user.enable_v2_search != use_v2:
        user.enable_v2_search = use_v2
        user.save()

    return redirect(next)
