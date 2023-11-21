from typing import Literal, Tuple

from django import template
from django.core.paginator import Paginator

from search import search as search_vectors

# from silk.profiling.profiler import silk_profile


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
# @silk_profile(name="Search.TemplateTag.category")
def search_category(context, *, category, limit=None, show_heading=False):
    request = context["request"]
    query = context["search_query"]
    page = int(context["page"])

    search_vector = SEARCH_VECTORS[category](request)

    # `list` needs to be called to force the database query to be evaluated
    # before passing the value to the paginator. If this isn't done, the
    # pages will have the pinned results removed after pagination and cause
    # the pages to have odd lengths.
    search_results = search_vector.search_results(query)
    search_results_count = search_results.count()

    if limit:
        search_results = search_results[: int(limit)]

    # Only paginate if there is no limit.
    if not limit:
        search_results_paginator = Paginator(search_results, PAGE_SIZE)
        search_results = search_results_paginator.page(page)

    # The singular/plural of the result type we can tell users about in
    # headings, errors etc
    result_type_display, result_type_display_plural = _get_result_type_displays(
        category
    )

    pinned_results = []
    if page == 1:
        pinned_results = search_vector.pinned(query)

    total_count = search_results_count + len(pinned_results)

    if total_count != 1:
        result_type_display = result_type_display_plural
    return {
        "request": request,
        "perms": context["perms"],
        "search_category": category,
        "search_results_item_template": _get_result_template(category),
        "pinned_results": pinned_results,
        "num_pinned_results": f"{len(pinned_results)}",
        "search_results": search_results,
        "search_query": query,
        "count": total_count,
        "show_heading": show_heading,
        "result_type_display": result_type_display,
        "is_limited": limit is not None and total_count > limit,
    }


@register.simple_tag(takes_context=True)
# @silk_profile(name="Search.TemplateTag.count")
def search_count(context, *, category):
    request = context["request"]
    query = context["search_query"]

    search_vector = SEARCH_VECTORS[category](request)
    hits = search_vector.search(query).count()

    # combined total for not just pages but people and teams
    if category == "all_pages":
        search_vector = SEARCH_VECTORS["people"](request)
        hits += search_vector.search(query).count()
        search_vector = SEARCH_VECTORS["teams"](request)
        hits += search_vector.search(query).count()

    return hits


def _get_result_template(category: SearchCategory) -> str:
    page_categories = ("all_pages", "guidance", "tools", "news")

    if category in page_categories:
        return "search/partials/result/page.html"

    return f"search/partials/result/{category}.html"


def _get_result_type_displays(category: SearchCategory) -> Tuple[str, str]:
    category_result_types_mapping = {
        "all_pages": ("page", "pages"),
        "people": ("person", "people"),
        "teams": ("team", "teams"),
        "guidance": ("guidance page", "guidance pages"),
        "tools": ("tool", "tools"),
        "news": ("news item", "news items"),
    }

    return category_result_types_mapping[category]
