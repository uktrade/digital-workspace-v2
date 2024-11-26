from typing import Any

from django.conf import settings
from django.db.models.query import QuerySet
from django.views.generic import ListView

from peoplefinder.models import Person, Team
from search.search import PeopleSearchVector


class PeopleDirectory(ListView):
    model = Person
    template_name = "peoplefinder/person-directory.html"
    paginate_by = 30

    def dispatch(self, request, *args, **kwargs):
        self.query = self.request.GET.get("query", "")

        self.team = None
        if team_pk := self.request.GET.get("team", ""):
            self.team = Team.objects.get(pk=team_pk)

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Any]:
        if self.query:
            people_results = PeopleSearchVector(self.request).search(
                query_str=self.query
            )
            person_ids = [p.id for p in people_results]
            queryset = Person.objects.filter(id__in=person_ids)
        else:
            queryset = super().get_queryset()
            if not self.request.user.has_perm(
                "peoplefinder.can_view_inactive_profiles"
            ):
                days = settings.SEARCH_SHOW_INACTIVE_PROFILES_WITHIN_DAYS
                queryset = queryset.active_or_inactive_within(days=days)

        if self.team:
            queryset = queryset.filter(
                roles__team__pk__in=[self.team.pk]
                + [tt.child.pk for tt in self.team.parents.all()]
            )
            print(self.team.parents.all())
            print(self.team.children.all())

        return queryset

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        page_title = "Find people"

        if self.team:
            page_title = f"Find people in {self.team}"

        context.update(
            page_title=page_title,
            team=self.team,
            team_breadcrumbs=True,
            extra_breadcrumbs=[
                (None, "People directory"),
            ],
            search_query=self.request.GET.get("query", ""),
        )
        return context
