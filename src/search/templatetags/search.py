from typing import Literal, Tuple

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
    context, *, category, tab_name=None, limit=None, show_heading=False
):
    request = context["request"]
    query = context["search_query"]
    page = context["page"]

    search_vector = SEARCH_VECTORS[category](request)
    pinned_results = search_vector.pinned(query)
    # `list` needs to be called to force the database query to be evaluated
    # before passing the value to the paginator. If this isn't done, the
    # pages will have the pinned results removed after pagination and cause
    # the pages to have odd lengths.
    search_results = list(pinned_results) + list(search_vector.search(query))
    count = len(search_results)

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
    if count != 1:
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
        "search_query": query,
        "count": count,
        "show_heading": show_heading,
        "result_type_display": result_type_display,
        "is_limited": limit is not None and count > limit,
    }


# Method for querying using wagtails default autocomplete functionality
#
def autocomplete(request, query, all_results=False):
    limit = 3
    search_results = {}

    if all_results:
        search_results.update(
            {"pages": list(SEARCH_VECTORS["all_pages"](request).autocomplete(query))}
        )
        search_results.update(
            {"people": list(SEARCH_VECTORS["people"](request).autocomplete(query))}
        )
        search_results.update(
            {"teams": list(SEARCH_VECTORS["teams"](request).autocomplete(query))}
        )
    else:
        search_results.update(
            {
                "tools": list(
                    SEARCH_VECTORS["tools"](request).autocomplete(query)[:limit]
                )
            }
        )
        search_results.update(
            {
                "pages": list(
                    SEARCH_VECTORS["all_pages"](request).autocomplete(query)[:limit]
                )
            }
        )
        search_results.update(
            {
                "people": list(
                    SEARCH_VECTORS["people"](request).autocomplete(query)[:limit]
                )
            }
        )
        search_results.update(
            {
                "teams": list(
                    SEARCH_VECTORS["teams"](request).autocomplete(query)[:limit]
                )
            }
        )

    return search_results


@register.simple_tag(takes_context=True)
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
