# from typing import Literal, Tuple

from django import template
from django.core.paginator import Paginator

from search import search as search_vectors
from search.templatetags import search as main_search


register = template.Library()


SEARCH_VECTORS: dict[str, search_vectors.SearchVector] = {
    "all_pages": search_vectors.AllPagesSearchVector,
    "people": search_vectors.PeopleSearchVector,
    "teams": search_vectors.TeamsSearchVector,
    "guidance": search_vectors.GuidanceSearchVector,
    "tools": search_vectors.ToolsSearchVector,
    "news": search_vectors.NewsSearchVector,
}


@register.inclusion_tag(
    "search/partials/search_results_explore.html", takes_context=True
)
def search_category(context, *, category, limit=None, show_heading=False):
    request = context["request"]
    query = context["search_query"]
    page = context["page"]

    search_vector = SEARCH_VECTORS[category](request)
    search_results = search_vector.search(query)
    count = search_results.count()

    search_results_paginator = Paginator(search_results, main_search.PAGE_SIZE)
    search_results = search_results_paginator.page(page)

    (
        result_type_display,
        result_type_display_plural,
    ) = main_search._get_result_type_displays(category)
    if count != 1:
        result_type_display = result_type_display_plural

    return {
        "request": request,
        "search_category": category,
        "search_results_item_template": "search/partials/result/explore.html",
        "pinned_results": [],
        "num_pinned_results": "0",
        "search_results": search_results,
        "search_query": query,
        "count": count,
        "show_heading": show_heading,
        "result_type_display": result_type_display,
        "is_limited": limit is not None and count > limit,
    }


@register.simple_tag
def score(obj):
    return round(getattr(obj, "_score", "-"), 2)
