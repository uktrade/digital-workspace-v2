from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import render
from wagtail.core.models import Page
from wagtail.search.models import Query


def search(request):
    search_query = request.GET.get("query", None)
    page = request.GET.get("page", 1)

    # Search
    if search_query:
        # Check for quoted phrase
        if search_query.startswith('"') and search_query.endswith('"'):
            search_results = Page.objects.live().search(search_query.lower(), operator='and')
        else:
            search_results = Page.objects.live().search(search_query.lower())

        query = Query.get(search_query.lower())

        # Record hit
        query.add_hit()
    else:
        search_results = Page.objects.none()

    # Pagination
    paginator = Paginator(search_results, 10)

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
