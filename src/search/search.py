from content.models import ContentPage, ContentPageIndexManager
from news.models import NewsPage
from peoplefinder.models import Person, Team, PersonIndexManager, TeamIndexManager
from tools.models import Tool
from working_at_dit.models import PoliciesAndGuidanceHome

from extended_search.managers import get_search_query


class SearchVector:
    def __init__(self, request, annotate_score=False):
        self.request = request
        self.annotate_score = annotate_score

    def _wagtail_search(self, queryset, query, *args, **kwargs):
        """
        Allows e.g. score annotation without polluting overriden search method
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

    def pinned(self, query):
        return self.get_queryset().pinned(query)

    def search(self, query, *args, **kwargs):
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

    def search(self, query, *args, **kwargs):
        queryset = self.get_queryset()
        return self._wagtail_search(queryset, query, *args, **kwargs)


class TeamsSearchVector(SearchVector):
    def get_queryset(self):
        return Team.objects.all().with_all_parents()


#
# New vectors for complex search alongside v2 - should get rolled in at end of
# the indexing improvements workstream. Need to be alongside to run v2 and v2.5
# queries side by side, e.g. for "explore" page
#


class NewAllPagesSearchVector(AllPagesSearchVector):
    def _wagtail_search(self, queryset, query, *args, **kwargs):
        return queryset.search(
            query, *args, partial_match=False, **kwargs
        ).annotate_score("_score")

    def search(self, query, *args, **kwargs):
        query = get_search_query(
            ContentPageIndexManager, query, ContentPage, *args, **kwargs
        )
        return self._wagtail_search(self.get_queryset(), query, *args, **kwargs)


class NewGuidanceSearchVector(GuidanceSearchVector):
    ...


class NewNewsSearchVector(NewsSearchVector):
    ...


class NewToolsSearchVector(ToolsSearchVector):
    ...


class NewPeopleSearchVector(PeopleSearchVector):
    def _wagtail_search(self, queryset, query, *args, **kwargs):
        return queryset.search(
            query, *args, partial_match=False, **kwargs
        ).annotate_score("_score")

    def search(self, query, *args, **kwargs):
        queryset = self.get_queryset()
        query = get_search_query(PersonIndexManager, query, Person, *args, **kwargs)
        return self._wagtail_search(queryset, query, *args, **kwargs)


class NewTeamsSearchVector(TeamsSearchVector):
    def _wagtail_search(self, queryset, query, *args, **kwargs):
        return queryset.search(
            query, *args, partial_match=False, **kwargs
        ).annotate_score("_score")

    def search(self, query, *args, **kwargs):
        queryset = self.get_queryset()
        query = get_search_query(TeamIndexManager, query, Team, *args, **kwargs)
        return self._wagtail_search(queryset, query, *args, **kwargs)
