from typing import Literal

from django import template
from django.core.paginator import Paginator

from search import search as search_vectors


register = template.Library()

SearchCategory = Literal["all", "people", "teams", "guidance", "tools", "news"]

SEARCH_CATEGORIES: set[SearchCategory] = {
    "all",
    "people",
    "teams",
    "guidance",
    "tools",
    "news",
}
SEARCH_VECTORS: dict[str, search_vectors.SearchVector] = {
    "all_pages": search_vectors.AllPagesSearchVector,
    "people": search_vectors.PeopleSearchVector,
    "teams": search_vectors.TeamsSearchVector,
    "guidance": search_vectors.GuidanceSearchVector,
    "tools": search_vectors.ToolsSearchVector,
    "news": search_vectors.NewsSearchVector,
}
PAGE_SIZE = 20


@register.inclusion_tag(
    "search/partials/search_results_category.html", takes_context=True
)
def search_category(
    context, *, category, limit=None, heading=None, heading_plural=None
):
    request = context["request"]
    query = context["search_query"]
    page = context["page"]

    search_vector = SEARCH_VECTORS[category](request)
    pinned_results = search_vector.pinned(query)
    # `list` needs to be called to force the database query to be evaluated before
    # passing the value to the paginator. If this isn't done, the pages will have the
    # pinned results removed after pagination and cause the pages to have odd lengths.
    search_results = list(search_vector.search(query))
    count = len(search_results)

    if limit:
        search_results = search_results[: int(limit)]

    # Only paginate if there is no limit.
    if not limit:
        search_results_paginator = Paginator(search_results, PAGE_SIZE)
        search_results = search_results_paginator.page(page)

    if heading and (count > 1 or count == 0):
        heading = heading_plural or f"{heading}s"

    return {
        "request": request,
        "search_category": category,
        "search_results_item_template": _get_result_template(category),
        "pinned_results": pinned_results,
        "num_pinned_results": len(pinned_results),
        "search_results": search_results,
        "search_query": query,
        "count": count,
        "heading": heading,
        "is_limited": limit is not None and count > limit,
    }


@register.simple_tag(takes_context=True)
def search_count(context, *, category):
    request = context["request"]
    query = context["search_query"]

    search_vector = SEARCH_VECTORS[category](request)
    hits = search_vector.search(query).count()

    return hits


def _get_result_template(category: SearchCategory) -> str:
    page_categories = ("all_pages", "guidance", "tools", "news")

    if category in page_categories:
        return "search/partials/result/page.html"

    return f"search/partials/result/{category}.html"
