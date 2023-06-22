from django.conf import settings
from wagtail.search.query import Boost, Fuzzy, Phrase, PlainText, MATCH_NONE


from content.models import ContentPage
from news.models import NewsPage
from peoplefinder.models import Person, Team
from tools.models import Tool
from search_extended.settings import search_extended_settings
from search_extended.types import AnalysisType, SearchQueryType
from working_at_dit.models import PoliciesAndGuidanceHome

from typing import Any, Collection, Dict


class SearchVector():

    def __init__(self, request, annotate_score=False):
        self.request = request
        self.annotate_score = annotate_score

    def _wagtail_search(self, queryset, query, *args, **kwargs):
        """
        Allows e.g. score annotation without polluting overriden search method
        """
        if self.annotate_score:
            return (
                queryset
                .search(query, *args, **kwargs)
                .annotate_score("_score")
            )

        return queryset.search(query, *args, **kwargs)

    def get_queryset(self):
        raise NotImplementedError

    def pinned(self, query):
        return []

    def search(self, query, *args, **kwargs):
        queryset = self.get_queryset()
        return self._wagtail_search(queryset, query, *args, **kwargs)


class PagesSearchVector(SearchVector):
    page_model = None

    def get_queryset(self):
        return self.page_model.objects.public().live()

    def pinned(self, query):
        return self.get_queryset().pinned(query)

    def search(self, query, *args, **kwargs):
        query, args, kwargs = self.page_model.get_all_searchqueries(
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

    def search(self, query, *args, **kwargs):
        query, args, kwargs = Person.get_all_searchqueries(
            query,
            *args,
            **kwargs
        )
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
    pass
    # field_mapping = {
    #     "search_title": {
    #         "boost_key": "PAGE_TITLE",
    #         "analysis": [
    #             AnalysisType.TOKENIZED,
    #             AnalysisType.EXPLICIT,
    #         ],
    #         "queries": [
    #             SearchQueryType.PHRASE,
    #             SearchQueryType.QUERY_AND,
    #             SearchQueryType.QUERY_OR
    #         ]
    #     },
    #     "search_headings": {
    #         "boost_key": "PAGE_HEADINGS",
    #         "analysis": [
    #             AnalysisType.TOKENIZED,
    #             AnalysisType.EXPLICIT,
    #         ],
    #         "queries": [
    #             SearchQueryType.PHRASE,
    #             SearchQueryType.QUERY_AND,
    #             SearchQueryType.QUERY_OR
    #         ]
    #     },
    #     "search_excerpt": {
    #         "boost_key": "PAGE_EXCERPT",
    #         "analysis": [
    #             AnalysisType.TOKENIZED,
    #             AnalysisType.EXPLICIT,
    #         ],
    #         "queries": [
    #             SearchQueryType.PHRASE,
    #             SearchQueryType.QUERY_AND,
    #             SearchQueryType.QUERY_OR
    #         ]
    #     },
    #     "search_content": {
    #         "boost_key": "PAGE_CONTENT",
    #         "analysis": [
    #             AnalysisType.TOKENIZED,
    #             AnalysisType.EXPLICIT,
    #         ],
    #         "queries": [
    #             SearchQueryType.PHRASE,
    #             SearchQueryType.QUERY_AND,
    #             SearchQueryType.QUERY_OR
    #         ]
    #     },
    # }

    # def build_query(
    #     self,
    #     query: str,
    #     *args,
    #     **kwargs
    # ):
    #     search_queries = self.get_all_searchqueries(query)
    #     fuzzy = Boost(
    #         Fuzzy(query),
    #         search_extended_settings.get_boost_value("SEARCH_FUZZY")
    #     )
    #     # Fuzzy requires partials off
    #     kwargs['partial_match'] = False

    #     return (
    #         search_queries |
    #         fuzzy
    #     ), args, kwargs

    # def search(self, query, *args, **kwargs):
    #     query, args, kwargs = self.build_query(
    #         query,
    #         *args,
    #         operator="and",
    #         **kwargs
    #     )
    #     # @TODO needs working on
    #     queryset = self.get_queryset()  # removed  pinning / unpinning
    #     return self._wagtail_search(queryset, query, *args, **kwargs)


class NewGuidanceSearchVector(GuidanceSearchVector):
    pass


class NewNewsSearchVector(NewsSearchVector):
    pass


class NewToolsSearchVector(ToolsSearchVector):
    pass


class NewPeopleSearchVector(PeopleSearchVector):

    def search(self, query, *args, **kwargs):
        queryset = self.get_queryset()
        query = Person.objects.get_search_query(query, *args, **kwargs)
        return self._wagtail_search(queryset, query, *args, **kwargs)

    # field_mapping = {
    #     "full_name": {
    #         "boost_key": "PERSON_NAME",
    #         "analysis": [
    #             AnalysisType.TOKENIZED,
    #             AnalysisType.EXPLICIT,
    #         ],
    #         "queries": [
    #             SearchQueryType.PHRASE,
    #             SearchQueryType.QUERY_AND,
    #             SearchQueryType.QUERY_OR,
    #         ]
    #     },
    #     "email": {
    #         "boost_key": "PERSON_EMAIL_PHONE",
    #         "analysis": [
    #             AnalysisType.KEYWORD,
    #         ],
    #         "queries": [
    #             SearchQueryType.PHRASE,
    #         ]
    #     },
    #     "contact_email": {
    #         "boost_key": "PERSON_EMAIL_PHONE",
    #         "analysis": [
    #             AnalysisType.KEYWORD,
    #         ],
    #         "queries": [
    #             SearchQueryType.PHRASE,
    #         ]
    #     },
    #     "primary_phone_number": {
    #         "boost_key": "PERSON_EMAIL_PHONE",
    #         "analysis": [
    #             AnalysisType.KEYWORD,
    #         ],
    #         "queries": [
    #             SearchQueryType.PHRASE,
    #         ]
    #     },
    #     "secondary_phone_number": {
    #         "boost_key": "PERSON_EMAIL_PHONE",
    #         "analysis": [
    #             AnalysisType.KEYWORD,
    #         ],
    #         "queries": [
    #             SearchQueryType.PHRASE,
    #         ]
    #     },
    #     "town_city_or_region": {
    #         "boost_key": "PERSON_LOCATION",
    #         "analysis": [
    #             AnalysisType.TOKENIZED,
    #         ],
    #         "queries": [
    #             SearchQueryType.PHRASE,
    #             SearchQueryType.QUERY_AND,
    #             SearchQueryType.QUERY_OR,
    #         ]
    #     },
    #     "regional_building": {
    #         "boost_key": "PERSON_LOCATION",
    #         "analysis": [
    #             AnalysisType.TOKENIZED,
    #         ],
    #         "queries": [
    #             SearchQueryType.PHRASE,
    #             SearchQueryType.QUERY_AND,
    #             SearchQueryType.QUERY_OR,
    #         ]
    #     },
    #     "international_building": {
    #         "boost_key": "PERSON_LOCATION",
    #         "analysis": [
    #             AnalysisType.TOKENIZED,
    #         ],
    #         "queries": [
    #             SearchQueryType.PHRASE,
    #             SearchQueryType.QUERY_AND,
    #             SearchQueryType.QUERY_OR,
    #         ]
    #     },
    #     "fluent_languages": {
    #         "boost_key": "PERSON_LANGUAGES",
    #         "analysis": [
    #             AnalysisType.TOKENIZED,
    #         ],
    #         "queries": [
    #             SearchQueryType.PHRASE,
    #             SearchQueryType.QUERY_AND,
    #             SearchQueryType.QUERY_OR,
    #         ]
    #     },
    #     "search_teams": {
    #         "boost_key": "PERSON_TEAM",
    #         "analysis": [
    #             AnalysisType.TOKENIZED,
    #             AnalysisType.EXPLICIT,
    #         ],
    #         "queries": [
    #             SearchQueryType.PHRASE,
    #             SearchQueryType.QUERY_AND,
    #             SearchQueryType.QUERY_OR,
    #         ]
    #     },
    #     "profile_completion_amount": {
    #         "boost_key": "PERSON_PROFILE_COMPLETENESS",
    #         "analysis": [
    #             AnalysisType.PROXIMITY,
    #         ],
    #     },
    #     "has_photo": {
    #         "boost_key": "PERSON_HAS_PHOTO",
    #         "analysis": [
    #             AnalysisType.PROXIMITY,
    #         ],
    #     },
    #     "roles": {
    #         "boost_key": "PERSON_ROLE",
    #         "analysis": [
    #             AnalysisType.TOKENIZED,
    #             AnalysisType.EXPLICIT,
    #         ],
    #         "queries": [
    #             SearchQueryType.PHRASE,
    #             SearchQueryType.QUERY_AND,
    #             SearchQueryType.QUERY_OR,
    #         ]
    #     },
    #     "key_skills": {
    #         "boost_key": "PERSON_SKILLS",
    #         "analysis": [
    #             AnalysisType.TOKENIZED,
    #             AnalysisType.EXPLICIT,
    #         ],
    #         "queries": [
    #             SearchQueryType.PHRASE,
    #             SearchQueryType.QUERY_AND,
    #             SearchQueryType.QUERY_OR,
    #         ]
    #     },
    #     "learning_interests": {
    #         "boost_key": "PERSON_INTERESTS",
    #         "analysis": [
    #             AnalysisType.TOKENIZED,
    #         ],
    #         "queries": [
    #             SearchQueryType.PHRASE,
    #             SearchQueryType.QUERY_AND,
    #             SearchQueryType.QUERY_OR,
    #         ]
    #     },
    #     "additional_roles": {
    #         "boost_key": "PERSON_ADDITIONAL_ROLES",
    #         "analysis": [
    #             AnalysisType.TOKENIZED,
    #             AnalysisType.EXPLICIT,
    #         ],
    #         "queries": [
    #             SearchQueryType.PHRASE,
    #             SearchQueryType.QUERY_AND,
    #             SearchQueryType.QUERY_OR,
    #         ]
    #     },
    #     "networks": {
    #         "boost_key": "PERSON_NETWORKS",
    #         "analysis": [
    #             AnalysisType.TOKENIZED,
    #             AnalysisType.EXPLICIT,
    #         ],
    #         "queries": [
    #             SearchQueryType.PHRASE,
    #             SearchQueryType.QUERY_AND,
    #             SearchQueryType.QUERY_OR,
    #         ]
    #     },
    # }

    # def build_query(
    #     self,
    #     query: str,
    #     *args,
    #     **kwargs
    # ):
    #     search_queries = self.get_all_searchqueries(query)
    #     fuzzy = Boost(
    #         Fuzzy(query),
    #         search_extended_settings.get_boost_value("SEARCH_FUZZY")
    #     )
    #     # Fuzzy requires partials off
    #     kwargs['partial_match'] = False

    #     return (
    #         search_queries |
    #         fuzzy
    #     ), args, kwargs


class NewTeamsSearchVector(TeamsSearchVector):
    field_mapping = {
        "search_title": {
            "boost_key": "PAGE_TITLE",
            "analysis": [
                AnalysisType.TOKENIZED,
                AnalysisType.EXPLICIT,
            ],
            "queries": [
                SearchQueryType.PHRASE,
                SearchQueryType.QUERY_AND,
                SearchQueryType.QUERY_OR
            ]
        },
        "search_headings": {
            "boost_key": "PAGE_HEADINGS",
            "analysis": [
                AnalysisType.TOKENIZED,
                AnalysisType.EXPLICIT,
            ],
            "queries": [
                SearchQueryType.PHRASE,
                SearchQueryType.QUERY_AND,
                SearchQueryType.QUERY_OR
            ]
        },
        "search_excerpt": {
            "boost_key": "PAGE_EXCERPT",
            "analysis": [
                AnalysisType.TOKENIZED,
                AnalysisType.EXPLICIT,
            ],
            "queries": [
                SearchQueryType.PHRASE,
                SearchQueryType.QUERY_AND,
                SearchQueryType.QUERY_OR
            ]
        },
        "search_content": {
            "boost_key": "PAGE_CONTENT",
            "analysis": [
                AnalysisType.TOKENIZED,
                AnalysisType.EXPLICIT,
            ],
            "queries": [
                SearchQueryType.PHRASE,
                SearchQueryType.QUERY_AND,
                SearchQueryType.QUERY_OR
            ]
        },
    }

    def build_query(
        self,
        query: str,
        *args,
        **kwargs
    ):
        search_queries = self.get_all_searchqueries(query)
        fuzzy = Boost(
            Fuzzy(query),
            search_extended_settings.get_boost_value("SEARCH_FUZZY")
        )
        # Fuzzy requires partials off
        kwargs['partial_match'] = False

        return (
            search_queries |
            fuzzy
        ), args, kwargs
