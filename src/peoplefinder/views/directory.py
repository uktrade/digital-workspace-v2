from typing import Any

from django.db.models.query import QuerySet
from django.views.generic import ListView

from peoplefinder.models import Person
from search.search import PeopleSearchVector


class PeopleDirectory(ListView):
    model = Person
    template_name = "peoplefinder/person-directory.html"
    paginate_by = 60

    def get_queryset(self) -> QuerySet[Any]:
        people_results = PeopleSearchVector(self.request).search(
            query_str=self.request.GET.get("query", "")
        )
        return people_results

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
