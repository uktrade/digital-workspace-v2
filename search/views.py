import logging
import math
import shlex
from typing import Optional, TypedDict

from django import forms
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.template.response import TemplateResponse
from django.views.decorators.http import require_http_methods
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

from content.models import ContentPage, SearchExclusionPageLookUp, SearchPinPageLookUp

from .forms import SearchCategory, SearchForm
from .search import sanitize_search_query, search_all


logger = logging.getLogger(__name__)


def search(request):
    page = int(request.GET.get("page", 1))
    search_query = request.GET.get("query", None)

    if search_query is None:
        search_query = request.GET.get("s", None)

    previous_page = None
    next_page = None
    total_shown = 10

    # OR based search apart from anything quoted
    sanitized_search_query = sanitize_search_query(search_query)
    print("*************************")
    print(sanitized_search_query)

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


class V2SearchContext(TypedDict):
    search_query: Optional[str]
    search_category: Optional[str]
    search_categories: type[SearchCategory]
    page_results: list
    team_results: list
    people_results: list
    results: list
    results_template: Optional[str]
    total_matches: int
    # Must be provided before passing to the response.
    form: Optional[forms.Form]


@require_http_methods(["GET"])
def v2_search(request: HttpRequest) -> HttpResponse:
    query = request.GET.get("query")
    category = request.GET.get("category")

    if category:
        category = category if category in SearchCategory else None

    context: V2SearchContext = {
        "search_query": query,
        "search_category": category,
        "search_categories": SearchCategory,
        "page_results": [],
        "team_results": [],
        "people_results": [],
        "results": [],
        "results_template": None,
        "total_matches": 0,
        "form": None,
    }

    if query:
        form = SearchForm(data=request.GET)
        form.is_valid()

        (
            context["page_results"],
            context["team_results"],
            context["people_results"],
        ) = search_all(request, query, category)
    else:
        form = SearchForm()

    if category == "pages":
        context["results"] = context["page_results"]
        context["results_template"] = "search/partials/page_results.html"
    elif category == "teams":
        context["results"] = context["team_results"]
        context["results_template"] = "search/partials/team_results.html"
    elif category == "people":
        context["results"] = context["people_results"]
        context["results_template"] = "search/partials/people_results.html"

    if category:
        context["total_matches"] = len(context["results"])
    else:
        context["total_matches"] = sum(
            [
                len(x)
                for x in [
                    context["page_results"],
                    context["team_results"],
                    context["people_results"],
                ]
            ]
        )

    context["form"] = form

    assert context["form"], "The form must be provided before passing to the response"

    # We must return a `TemplateResponse` because there is middleware which uses the
    # `process_template_response` hook.
    return TemplateResponse(request, "search/v2_search.html", context=context)
