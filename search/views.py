from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import render

from .engines import wordpress


def search_global(request):
    query = request.GET.get("query", None)

    if not query:
        return render(request, "search/index.html")

    wordpress_results = wordpress.search(query, per_page=5)

    has_results = len(wordpress_results)

    return render(request, "search/results_global.html", {
        "query": query,
        "querystring": request.GET.urlencode,
        "has_results": has_results,
        "wordpress_results": wordpress_results,
        "wordpress_num_results": len(wordpress_results),
        "wordpress_has_more_results": len(wordpress_results) > 5
    })


def search_wordpress(request):
    query = request.GET.get("query", None)
    page = request.GET.get("page", 1)

    if query:
        results = wordpress.search(query, page=page)
    else:
        results = []

    paginator = Paginator(results, 10)
    try:
        results = paginator.page(page)
    except PageNotAnInteger:
        results = paginator.page(1)
    except EmptyPage:
        results = paginator.page(paginator.num_pages)

    return render(request, "search/results_wordpress.html", {
        "query": query,
        "querystring": request.GET.urlencode,
        "results": results,
        "num_pages": paginator.num_pages,
        "num_results": paginator.count
    })
