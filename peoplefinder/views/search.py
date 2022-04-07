from django.template.response import TemplateResponse
from django.views.decorators.http import require_http_methods

from peoplefinder.forms.search import PEOPLE_FILTER, TEAMS_FILTER, SearchForm
from peoplefinder.models import Team
from peoplefinder.services.search import search


@require_http_methods(["GET"])
def search_view(request):
    query = request.GET.get("query")
    filters = request.GET.getlist("filters", [TEAMS_FILTER, PEOPLE_FILTER])

    context = {
        "team_matches": [],
        "person_matches": [],
        "total_matches": 0,
    }

    if query:
        form = SearchForm(data=request.GET)
        form.is_valid()

        team_matches, person_matches = search(**form.cleaned_data)

        if team_matches:
            team_parents = {
                team["pk"]: team
                for team in Team.objects.with_all_parents().filter(
                    pk__in=[x.pk for x in team_matches]
                )
            }

            for team in team_matches:
                team.all_parents = team_parents[team.pk]["all_parents"][:-1]

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
    }

    # We must return a `TemplateResponse` because there is middleware which uses the
    # `process_template_response` hook.
    return TemplateResponse(request, "peoplefinder/search.html", context=context)
