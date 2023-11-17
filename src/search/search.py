from django.core.cache import cache

from content.models import ContentPage
from extended_search.managers.query_builder import CustomQueryBuilder
from extended_search.query import swap_variables
from news.models import NewsPage
from peoplefinder.models import Person, Team
from tools.models import Tool
from working_at_dit.models import PoliciesAndGuidanceHome


class SearchVector:
    def __init__(self, request, annotate_score=False):
        self.request = request
        self.annotate_score = annotate_score

    def _wagtail_search(self, queryset, query_str, *args, **kwargs):
        """
        Allows e.g. score annotation without polluting overridden search method
        """
        return_method = queryset.search(query_str, *args, **kwargs)

        if self.annotate_score:
            return_method = return_method.annotate_score("_score")

        return return_method

    def get_queryset(self):
        raise NotImplementedError

    def search(self, query_str, *args, **kwargs):
        queryset = self.get_queryset()
        return self._wagtail_search(queryset, query_str, *args, **kwargs)

    def search_results(self, query_str, *args, **kwargs):
        return list(self.search(query_str))

    def count(self, query_str, *args, **kwargs):
        return len(self.search_results(query_str))

    def pinned(self, query):
        return []


class ModelSearchVector(SearchVector):
    model = None

    def get_queryset(self):
        return self.model.objects.all()

    def get_build_query_cache_key(self):
        return self.model.__name__

    def build_query(self, query_str, *args, **kwargs):
        built_query = cache.get(self.get_build_query_cache_key(), None)
        if not built_query:
            built_query = CustomQueryBuilder.build_search_query(self.model)
            cache.set(self.get_build_query_cache_key(), built_query, 60 * 60)
        return swap_variables(built_query, query_str)

    def search(self, query_str, *args, **kwargs):
        queryset = self.get_queryset()
        built_query = self.build_query(query_str, *args, **kwargs)
        return self._wagtail_search(queryset, built_query, *args, **kwargs)

    def get_search_results_cache_key(self, query_str):
        return type(self).__name__ + query_str.lower()

    def search_results(self, query_str, *args, **kwargs):
        # Try and get the cached results
        search_results = cache.get(self.get_search_results_cache_key(query_str), None)
        if search_results:
            return search_results

        search_results = super().search_results(query_str, *args, **kwargs)

        # Cache for 1 hour
        cache.set(self.get_search_results_cache_key(query_str), search_results, 60 * 60)
        return search_results


class PagesSearchVector(ModelSearchVector):
    def get_queryset(self):
        return super().get_queryset().public_or_login().live()

    def pinned(self, query_str):
        return self.get_queryset().pinned(query_str)

    def search(self, query_str, *args, **kwargs):
        queryset = self.get_queryset().not_pinned(query_str)
        built_query = self.build_query(query_str, *args, **kwargs)
        return self._wagtail_search(queryset, built_query, *args, **kwargs)


class AllPagesSearchVector(PagesSearchVector):
    model = ContentPage


class GuidanceSearchVector(PagesSearchVector):
    model = ContentPage

    def get_queryset(self):
        policies_and_guidance_home = PoliciesAndGuidanceHome.objects.first()

        return super().get_queryset().descendant_of(policies_and_guidance_home)


class NewsSearchVector(PagesSearchVector):
    model = NewsPage


class ToolsSearchVector(PagesSearchVector):
    model = Tool


class PeopleSearchVector(ModelSearchVector):
    model = Person

    def get_queryset(self):
        people = super().get_queryset()

        if not self.request.user.has_perm("peoplefinder.delete_person"):
            people = people.active()

        people = people.prefetch_related("key_skills", "additional_roles", "teams")

        return people


class TeamsSearchVector(ModelSearchVector):
    model = Team

    def get_queryset(self):
        return super().get_queryset().with_all_parents()
