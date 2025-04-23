from typing import Any

from django.conf import settings
from django.core import paginator
from django.db.models import OuterRef, Subquery
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.views.generic import ListView
from waffle import flag_is_active

from core import flags
from peoplefinder.filters import DiscoverFilters
from peoplefinder.models import Person, Team, TeamMember
from peoplefinder.services import directory as directory_service
from peoplefinder.services.team import TeamService


class PeopleDirectory(ListView):
    model = Person
    template_name = "peoplefinder/person-directory.html"
    paginate_by = 30

    def dispatch(self, request, *args, **kwargs):
        self.team = None
        if team_pk := self.request.GET.get("team", ""):
            self.team = Team.objects.get(pk=team_pk)

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Any]:
        queryset = super().get_queryset().select_related("uk_office_location")

        if not self.request.user.has_perm("peoplefinder.can_view_inactive_profiles"):
            days = settings.SEARCH_SHOW_INACTIVE_PROFILES_WITHIN_DAYS
            queryset = queryset.active_or_inactive_within(days=days)

        queryset = queryset.distinct()
        if self.team:
            queryset = queryset.filter(
                roles__team__pk__in=[self.team.pk]
                + [tt.child.pk for tt in self.team.parents.all()]
            )

        get_job_title_subquery = TeamMember.objects.filter(
            person=OuterRef("pk")
        ).values("job_title")
        queryset = queryset.annotate(job_title=Subquery(get_job_title_subquery[:1]))

        return queryset.order_by("first_name", "last_name")

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        page_title = "All people"

        if self.team:
            page_title = f"People in {self.team}"

        team_service = TeamService()
        root_team = team_service.get_root_team()

        context.update(
            page_title=page_title,
            team=self.team or root_team,
            team_breadcrumbs=True,
            extra_breadcrumbs=[
                (None, "People directory"),
            ],
            search_query=self.request.GET.get("query", ""),
            root_team=root_team,
            is_root_team=self.team == root_team,
        )
        return context


# Identity Service - discovery


def discover(request: HttpRequest) -> HttpResponse | HttpResponseRedirect:
    """
    If the pf_discover flag is enabled, returns the discover page with all the people
    the given user has permission to see.
    Otherwise, redirects to people-directory page.
    """
    if not flag_is_active(request, flags.PF_DISCOVER):
        return redirect("people-directory")

    people_set = directory_service.get_people(request.user)
    discover_filters = DiscoverFilters(request.GET, queryset=people_set)
    people = discover_filters.qs

    pr = paginator.Paginator(people, per_page=30)
    page: int = int(request.GET.get("page", default=1))
    try:
        paginator_page = pr.page(page)
    except paginator.EmptyPage:
        # would be nice to have some sort of mnessage with this
        return redirect("people-discover")

    context = {
        "page_title": "Discover",
        "pages": paginator_page,
        "extra_breadcrumbs": [
            (None, "Discover"),
        ],
        "discover_filters": discover_filters,
    }
    return render(request, "peoplefinder/discover.html", context)
