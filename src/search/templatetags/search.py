from typing import Literal, Tuple

from django import template
from django.conf import settings
from django.core.paginator import Paginator

from search import search as search_vectors


# from search.utils import has_only_bad_results
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
SEARCH_VECTORS: dict[str, search_vectors.ModelSearchVector] = {
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
def search_category(
    context,
    *,
    category,
    tab_name=None,
    limit=None,
    show_heading=False,
    show_bad_results_message=True,
):
    request = context["request"]
    query = context["search_query"]
    page = int(context["page"])

    search_vector = SEARCH_VECTORS[category](request)
    search_results = search_vector.search(query)
    search_results_count = get_count(context, category, query)

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
        "tab_name": tab_name,
        "tab_override": context["tab_override"],
        "search_query": query,
        "count": total_count,
        "is_results_count_low": total_count < settings.CUTOFF_SEARCH_RESULTS_VALUE,
        "show_bad_results_message": False,  # (
        #     show_bad_results_message
        #     and has_only_bad_results(
        #         query,
        #         category,
        #         pinned_results,
        #         search_results,
        #     )
        # ),
        "show_heading": show_heading,
        "result_type_display": result_type_display,
        "is_limited": limit is not None and total_count > limit,
    }


# Method for querying using wagtails default autocomplete functionality
#
def autocomplete(request, query):
    limit = 3
    search_results = {}

    search_results.update(
        {"tools": list(SEARCH_VECTORS["tools"](request).autocomplete(query)[:limit])}
    )
    search_results.update(
        {
            "pages": list(
                SEARCH_VECTORS["all_pages"](request).autocomplete(query)[:limit]
            )
        }
    )
    search_results.update(
        {"people": list(SEARCH_VECTORS["people"](request).autocomplete(query)[:limit])}
    )
    search_results.update(
        {"teams": list(SEARCH_VECTORS["teams"](request).autocomplete(query)[:limit])}
    )

    return search_results


def get_count(context, category, query):
    request = context["request"]

    if not hasattr(request, "extended_search_count_cache"):
        request.extended_search_count_cache = {}

    cached_count = request.extended_search_count_cache.get(category, None)
    if cached_count is not None:
        return cached_count

    search_vector = SEARCH_VECTORS[category](request)
    hits = search_vector.search(query).count()

    request.extended_search_count_cache[category] = hits
    return hits


@register.simple_tag(takes_context=True)
# @silk_profile(name="Search.TemplateTag.count")
def search_count(context, *, category):
    query = context["search_query"]
    hits = get_count(context, category, query)

    # combined total for not just pages but people and teams
    if category == "all_pages":
        hits += get_count(context, "people", query)
        hits += get_count(context, "teams", query)

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
