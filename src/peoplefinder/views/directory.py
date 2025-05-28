from typing import Any

from django.conf import settings
from django.core import paginator
from django.db.models import OuterRef, Subquery
from django.db.models.query import QuerySet
from django.forms import Field
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, QueryDict
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import ListView

from core import flags
from core.utils import flag_is_active
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


def get_url_for_removed_filter(
    request: HttpRequest, field: str | None = None, value: Any | None = None
) -> str:
    get_vars: QueryDict = request.GET.copy()

    # changing filters always means going back to page 1
    if "page" in get_vars.keys():
        get_vars.pop("page")

    if field is not None:
        current_field_values: list = get_vars.pop(field)
        current_field_values.remove(str(value))
        for val in current_field_values:
            get_vars.update({field: val})
    return request.build_absolute_uri(f"{request.path}?{get_vars.urlencode()}")


def get_display_label_value(field_name: str, field: Field, value: str):
    if value == "null":
        return "Not set"

    if field_name == "profile_completion":
        if value == "full":
            return "Complete"
        return "Incomplete"

    if field_name == "is_active":
        if value == "True":
            return "Active"
        return "Inactive"

    if field_name == "teams":
        for option in field.choices:
            if str(option[0]) == value:
                return option[1]
    return value


def discover(request: HttpRequest) -> HttpResponse | HttpResponseRedirect:
    """
    If the pf_discover flag is enabled, returns the discover page with all the people
    the given user has permission to see.
    Otherwise, redirects to people-directory page.
    """
    if not flag_is_active(request, flags.PF_DISCOVER):
        return redirect("people-directory")

    discover_filters = directory_service.get_people_with_filters(
        filter_options=request.GET, user=request.user
    )

    pr = paginator.Paginator(discover_filters.qs, per_page=30)
    page: int = int(request.GET.get("page", default=1))
    try:
        paginator_page = pr.page(page)
    except paginator.EmptyPage:
        paginator_page = None

    selected_filters = {
        field_name: {
            "label": discover_filters.form.fields[field_name].label,
            "values": [
                {
                    "label": get_display_label_value(
                        field_name=field_name,
                        field=discover_filters.form.fields[field_name],
                        value=value,
                    ),
                    "url": get_url_for_removed_filter(request, field_name, value),
                }
                for value in values
            ],
        }
        for field_name, values in discover_filters.applied_filters().items()
        if field_name != "sort_by"
    }

    context = {
        "page_title": "Find colleagues",
        "pages": paginator_page,
        "extra_breadcrumbs": [
            (None, "Discover"),
        ],
        "discover_filters": discover_filters,
        "selected_filters": selected_filters,
        "can_see_inactive_users": request.user.has_perm(
            "peoplefinder.can_view_inactive_profiles"
        ),
        "search_url": reverse("search:category", kwargs={"category": "people"}),
    }
    return render(request, "peoplefinder/discover.html", context)
