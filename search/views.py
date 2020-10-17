import shlex

from django.conf import settings
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import render
from wagtail.core.models import Page

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

from content.models import ContentPage
from content.models import (
    SearchExclusionPageLookUp,
    SearchPinPageLookUp,
)


def search(request):
    search_query = request.GET.get("query", None)
    # OR based search apart from anything quoted

    query_parts = shlex.split(search_query.lower())
    search_terms = ""

    for query_part in query_parts:
        # Check for phrases
        if " " in query_part:
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
            fields=[
                "content_contentpage__search_title",
                "content_contentpage__body_no_html"
            ]
            # default_field="title",
        ).highlight(
            'search_title',
            'content_contentpage__body_no_html',
            fragment_size=250,
        )

        print(make_search.to_dict())

        response = make_search.execute()

        exclusions = list(SearchExclusionPageLookUp.objects.filter(
            search_keyword_or_phrase__keyword_or_phrase__in=query_parts,
        ).values_list(
            'object_id',
            flat=True,
        ))

        hits = []

        for hit in response.hits:
            # TODO check which index the term was found in, if it's only title, no preview?
            if hit.pk not in exclusions:
                hits.append(hit)

        pinned = list(SearchPinPageLookUp.objects.filter(
            search_keyword_or_phrase__keyword_or_phrase__in=query_parts,
        ).values_list(
            'object_id',
            flat=True,
        ))

        # page_ids = [
        #     pid for pid in result_page_ids if int(pid) not in exclusions and int(pid) not in pinned
        # ]

        pinned_results = ContentPage.objects.live().filter(
            pk__in=pinned,
        )

        # search_results = ContentPage.objects.live().filter(
        #     pk__in=page_ids,
        # )
    else:
        search_results = [] #ContentPage.objects.none()

    # Pagination
    paginator = Paginator(hits, 10)

    # TODO Create preview text

    try:
        paginated_results = paginator.page(page)
    except PageNotAnInteger:
        paginated_results = paginator.page(1)
    except EmptyPage:
        paginated_results = paginator.page(paginator.num_pages)

    return render(request, "search/search.html", {
        "pinned_results": pinned_results,
        "num_results": pinned_results.count() + len(hits),
        "search_query": search_query,
        "search_results": paginated_results,
    })
