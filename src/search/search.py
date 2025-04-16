from django.conf import settings
from wagtail.search.query import Phrase

from content.models import BasePage
from extended_search.query_builder import CustomQueryBuilder
from news.models import NewsPage
from peoplefinder.models import Person, Team
from tools.models import Tool
from working_at_dit.models import PoliciesAndGuidanceHome


class SearchVector:
    def __init__(self, request):
        self.request = request

    def _wagtail_search(self, queryset, query_str, *args, **kwargs):
        """
        Allows base method overrides without polluting search method
        """
        return queryset.search(query_str, *args, **kwargs).annotate_score("_score")

    def _wagtail_autocomplete(self, queryset, query_str, *args, **kwargs):
        return queryset.autocomplete(query_str, *args, **kwargs)

    def get_queryset(self):
        raise NotImplementedError

    def search(self, query_str, *args, **kwargs):
        queryset = self.get_queryset()
        return self._wagtail_search(queryset, query_str, *args, **kwargs)

    def autocomplete(self, query_str, *args, **kwargs):
        queryset = self.get_queryset()
        return self._wagtail_autocomplete(queryset, query_str, *args, **kwargs)

    def pinned(self, query):
        return []


class ModelSearchVector(SearchVector):
    model = None

    def get_queryset(self):
        return self.model.objects.all()

    def build_query(self, query_str, *args, **kwargs):
        if query_str.startswith("EXACT_SEARCH "):
            if new_query_str := query_str[13:]:
                # A query beginning with `EXACT_SEARCH ` we search for an exact match.
                return Phrase(new_query_str)
        return CustomQueryBuilder.get_search_query(self.model, query_str)

    def search(self, query_str, *args, **kwargs):
        queryset = self.get_queryset()
        built_query = self.build_query(query_str, *args, **kwargs)
        return self._wagtail_search(queryset, built_query, *args, **kwargs)


class PagesSearchVector(ModelSearchVector):
    def get_queryset(self):
        return super().get_queryset().public_or_login().live().specific()

    def pinned(self, query_str):
        return self.get_queryset().pinned(query_str)

    def autocomplete(self, query_str, *args, **kwargs):
        queryset = self.get_queryset().not_pinned(query_str)
        return self._wagtail_autocomplete(queryset, query_str, *args, **kwargs)

    def search(self, query_str, *args, **kwargs):
        queryset = self.get_queryset().not_pinned(query_str)
        built_query = self.build_query(query_str, *args, **kwargs)
        return self._wagtail_search(queryset, built_query, *args, **kwargs)


class AllPagesSearchVector(PagesSearchVector):
    model = BasePage


class GuidanceSearchVector(PagesSearchVector):
    model = BasePage

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

        # Additional filters for normal users (none people admin/superusers).
        if not self.request.user.has_perm("peoplefinder.can_view_inactive_profiles"):
            days = settings.SEARCH_SHOW_INACTIVE_PROFILES_WITHIN_DAYS
            people = people.active_or_inactive_within(days=days)
        return people.prefetch_related("key_skills", "additional_roles", "teams")

    def autocomplete(self, query, *args, **kwargs):
        # never show inactive profiles on autocomplete
        queryset = Person.objects.all().active()
        return self._wagtail_autocomplete(queryset, query, *args, **kwargs)


class TeamsSearchVector(ModelSearchVector):
    model = Team

    def get_queryset(self):
        return super().get_queryset().with_all_parents()
