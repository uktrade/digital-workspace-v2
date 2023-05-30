from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from peoplefinder.forms.search import PEOPLE_FILTER, TEAMS_FILTER, SearchForm
from peoplefinder.services.search import search


# TODO[DWPF-454] remove this
@require_http_methods(["GET"])
def search_view(request):
    query = request.GET.get("query")

    return redirect(
        reverse("search:category", kwargs={"category": "people"})
        + f"?query={query}"
    )
