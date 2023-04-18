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
    filters = request.GET.getlist("filters", [TEAMS_FILTER, PEOPLE_FILTER])

    # users in the beta need to use the v2 search
    if request.user.enable_v2_search:
        return redirect(
            reverse("search:category", kwargs={"category": "people"})
            + f"?query={query}"
        )

    context = {
        "team_matches": [],
        "person_matches": [],
        "total_matches": 0,
    }

    if query:
        form = SearchForm(data=request.GET)
        form.is_valid()

        team_matches, person_matches = search(request, **form.cleaned_data)

        context |= {
            "team_matches": team_matches,
            "person_matches": person_matches,
            "total_matches": len(team_matches) + len(person_matches),
        }
    else:
        form = SearchForm()

    context |= {
        "people_and_teams_search_query": query,
        "people_and_teams_search_filters": filters,
        "query": query,
        "filters": filters,
        "form": form,
        "page": 1,
    }

    # We must return a `TemplateResponse` because there is middleware which uses the
    # `process_template_response` hook.
    return TemplateResponse(request, "peoplefinder/search.html", context=context)
