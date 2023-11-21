from extended_search.query_builder import CustomQueryBuilder

from content.models import ContentPage
from news.models import NewsPage
from peoplefinder.models import Person, Team
from tools.models import Tool

from working_at_dit.models import PoliciesAndGuidanceHome


class SearchVector:
    def __init__(self, request, annotate_score=False):
        self.request = request
        self.annotate_score = annotate_score

    def _wagtail_search(self, queryset, query, *args, **kwargs):
        """
        Allows e.g. score annotation without polluting overridden search method
        """
        return_method = queryset.search(query, *args, **kwargs)

        if self.annotate_score:
            return_method = return_method.annotate_score("_score")

        return return_method

    def get_queryset(self):
        raise NotImplementedError

    def search(self, query, *args, **kwargs):
        queryset = self.get_queryset()
        return self._wagtail_search(queryset, query, *args, **kwargs)

    def pinned(self, query):
        return []


class PagesSearchVector(SearchVector):
    page_model = None

    def get_queryset(self):
        return self.page_model.objects.public_or_login().live()

    def get_query(self, query_str):
        return CustomQueryBuilder.get_search_query(
            self.page_model,
            query_str,
        )

    def pinned(self, query):
        return self.get_queryset().pinned(query)

    def search(self, query, *args, **kwargs):
        queryset = self.get_queryset().not_pinned(query)
        query = self.get_query(query)
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

        # Additional filters for normal users (none people admin/superusers).
        if not self.request.user.has_perm("peoplefinder.can_view_inactive_profiles"):
            days = settings.SEARCH_SHOW_INACTIVE_PROFILES_WITHIN_DAYS
            people = people.active_or_inactive_within(days=days)

        people = people.prefetch_related("key_skills", "additional_roles", "teams")

        return people

    def search(self, query, *args, **kwargs):
        queryset = self.get_queryset()
        query = CustomQueryBuilder.get_search_query(
            Person,
            query,
            *args,
            **kwargs,
        )
        return self._wagtail_search(queryset, query, *args, **kwargs)


class TeamsSearchVector(SearchVector):
    def get_queryset(self):
        return Team.objects.all().with_all_parents()

    def search(self, query, *args, **kwargs):
        queryset = self.get_queryset()
        query = CustomQueryBuilder.get_search_query(Team, query, *args, **kwargs)
        return self._wagtail_search(queryset, query, *args, **kwargs)
