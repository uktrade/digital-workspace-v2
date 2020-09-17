import shlex

from django.conf import settings
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import render
from wagtail.core.models import Page

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search


def search(request):
    search_query = request.GET.get("query", None)
    # OR based search apart from anything quoted

    query_parts = shlex.split(search_query.lower())
    search_terms = ""

    for query_part in query_parts:
        # Check for phrases
        if " " in query_part:
            # phrase = ""
            # phrase_parts = query_part.split(" ")
            #
            # for phrase_part in phrase_parts:
            #     if phrase == "":
            #         phrase = phrase_part
            #     else:
            #         phrase = f"{phrase} AND {phrase_part}"

            query_part = f"\"{query_part}\""

        if search_terms == "":
            search_terms = query_part
        else:
            search_terms = f"{search_terms} OR {query_part}"

    page = request.GET.get("page", 1)

    if search_query:
        make_search = Search(
            index='wagtail__wagtailcore_page').using(
            Elasticsearch(
                settings.ELASTIC_SEARCH_URL,
            )
        ).query(
            "query_string",
            query=search_terms,
            default_field="_all_text",
        )

        response = make_search.execute()
        page_ids = []

        for hit in response.hits:
            # TODO check which index the term was found in, if it's only title, no preview
            page_ids.append(hit.pk)

        search_results = response.hits

        # search_results = Page.objects.live().filter(
        #     pk__in=page_ids,
        # )
    else:
        Page.objects.none()

    # Pagination
    paginator = Paginator(search_results, 10)

    # TODO Create preview text

    try:
        paginated_results = paginator.page(page)
    except PageNotAnInteger:
        paginated_results = paginator.page(1)
    except EmptyPage:
        paginated_results = paginator.page(paginator.num_pages)

    return render(request, "search/search.html", {
        "num_results": search_results.count(),
        "search_query": search_query,
        "search_results": paginated_results,
    })
