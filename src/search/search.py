from content.models import ContentPage
from news.models import NewsPage
from peoplefinder.models import Person, Team
from tools.models import Tool
from working_at_dit.models import PoliciesAndGuidanceHome

from typing import Any, Collection, Dict


class SearchVector:
    def __init__(self, request, annotate_score=False):
        self.request = request
        self.annotate_score = annotate_score
        print(f"annotate: {annotate_score}")

    def _wagtail_search(self, queryset, query, *args, **kwargs):
        """
        Allows e.g. score annotation without polluting overriden search method
        """
        if self.annotate_score:
            return queryset.search(query, *args, **kwargs).annotate_score("_score")

        return queryset.search(query, *args, **kwargs)

    def build_query(
        self,
        query: str,
        *args: Collection,
        **kwargs: Dict[str, Any]
    ) -> list[Any, list, Dict[str, Any]]:
        """
        Allows overriding of the query structure passed to the Wagtail
        "search()" method
        """
        return query, args, kwargs

    def get_queryset(self):
        raise NotImplementedError

    def pinned(self, query):
        return []

    def search(self, query, *args, **kwargs):
        query, args, kwargs = self.build_query(
            query,
            *args,
            operator="and",
            **kwargs
        )
        queryset = self.get_queryset()
        return self._wagtail_search(queryset, query, *args, **kwargs)


class PagesSearchVector(SearchVector):
    page_model = None

    def get_queryset(self):
        return self.page_model.objects.public().live()

    def pinned(self, query):
        return self.get_queryset().pinned(query)

    def search(self, query, *args, **kwargs):
        query, args, kwargs = self.build_query(
            query,
            *args,
            operator="and",
            **kwargs
        )
        queryset = self.get_queryset().not_pinned(query)
        return self._wagtail_search(queryset, query, *args, **kwargs)


class AllPagesSearchVector(PagesSearchVector):
    page_model = ContentPage


class GuidanceSearchVector(PagesSearchVector):
    page_model = ContentPage

    def get_queryset(self):
        policies_and_guidance_home = PoliciesAndGuidanceHome.objects.first()

        return super().get_queryset().descendant_of(policies_and_guidance_home)


class NewsSearchVector(PagesSearchVector):
    page_model = NewsPage


class ToolsSearchVector(PagesSearchVector):
    page_model = Tool


class PeopleSearchVector(SearchVector):
    def get_queryset(self):
        people = Person.objects.all()

        if not self.request.user.has_perm("peoplefinder.delete_person"):
            people = people.active()

        people = people.prefetch_related("key_skills", "additional_roles", "teams")

        return people


class TeamsSearchVector(SearchVector):
    def get_queryset(self):
        return Team.objects.all().with_all_parents()
