from typing import Any

from django.conf import settings
from django.db.models.query import QuerySet
from django.views.generic import ListView

from peoplefinder.models import Person
from search.search import PeopleSearchVector


class PeopleDirectory(ListView):
    model = Person
    template_name = "peoplefinder/person-directory.html"
    paginate_by = 30

    def get_queryset(self) -> QuerySet[Any]:
        query = self.request.GET.get("query", "")
        if query:
            people_results = PeopleSearchVector(self.request).search(
                query_str=self.request.GET.get("query", "")
            )
            return people_results

        queryset = super().get_queryset()

        if not self.request.user.has_perm("peoplefinder.can_view_inactive_profiles"):
            days = settings.SEARCH_SHOW_INACTIVE_PROFILES_WITHIN_DAYS
            queryset = queryset.active_or_inactive_within(days=days)
        return queryset

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            page_title="Find people",
            extra_breadcrumbs=[
                ("/", "Home"),
                (None, "People directory"),
            ],
            search_query=self.request.GET.get("query", ""),
        )
        return context
