from django.conf import settings
from wagtail.search.query import Boost, Fuzzy, Phrase, PlainText, MATCH_NONE

from enum import Enum

from content.models import ContentPage
from news.models import NewsPage
from peoplefinder.models import Person, Team
from tools.models import Tool
from search.backends.query import OnlyFields
from working_at_dit.models import PoliciesAndGuidanceHome

from typing import Any, Collection, Dict


class SearchQueryType(Enum):
    PHRASE = "P"
    QUERY_AND = "&"
    QUERY_OR = "|"
    FUZZY = "F"


class AnalysisType(Enum):
    EXPLICIT = "E"
    TOKENIZED = "T"
    KEYWORD = "K"
    PROXIMITY = "P"


class QueryBuilder:
    field_mapping = {}

    def _get_inner_searchquery_for_querytype(
        self,
        query_str: str,
        query_type: SearchQueryType,
    ):
        match query_type:
            case SearchQueryType.PHRASE:
                query = Phrase(query_str)
            case SearchQueryType.QUERY_AND:
                query = PlainText(query_str, operator="and")
            case SearchQueryType.QUERY_OR:
                query = PlainText(query_str, operator="or")
            case _:
                raise Exception
        return query

    def _get_boost_for_field_querytype_analysistype(
        self,
        base_field_name: str,
        query_type: SearchQueryType,
        analysis_type: AnalysisType,
    ):
        match query_type:
            case SearchQueryType.PHRASE:
                query_type_boost = "SEARCH_PHRASE"
            case SearchQueryType.QUERY_AND:
                query_type_boost = "SEARCH_QUERY_AND"
            case SearchQueryType.QUERY_OR:
                query_type_boost = "SEARCH_QUERY_OR"
            case SearchQueryType.FUZZY:
                query_type_boost = "SEARCH_FUZZY"
            case _:
                raise Exception

        match analysis_type:
            case AnalysisType.EXPLICIT:
                analysis_type_boost = "ANALYZER_EXPLICIT"
            case AnalysisType.TOKENIZED:
                analysis_type_boost = "ANALYZER_TOKENIZED"
            case AnalysisType.KEYWORD:
                analysis_type_boost = "ANALYZER_EXPLICIT"
            case AnalysisType.PROXIMITY:
                analysis_type_boost = 1.0  # @TODO figure out how to work this in
            case _:
                raise Exception

        field_boost = self.field_mapping[base_field_name]["boost_key"]

        return (
            settings.SEARCH_BOOST_VARIABLES[query_type_boost] *
            settings.SEARCH_BOOST_VARIABLES[analysis_type_boost] *
            settings.SEARCH_BOOST_VARIABLES[field_boost]
        )

    def _get_searchquery_for_query_field_querytype_analysistype(
        self,
        query_str: str,
        base_field_name: str,
        query_type: SearchQueryType,
        analysis_type: AnalysisType,
    ):
        query = self._get_inner_searchquery_for_querytype(query_str, query_type)

        boost = self._get_boost_for_field_querytype_analysistype(base_field_name, query_type, analysis_type)

        field_name = base_field_name
        if analysis_type == AnalysisType.EXPLICIT:
            field_name += "_explicit"

        return OnlyFields(Boost(query, boost), fields=[field_name])

    def _get_all_searchqueries_for_field(
        self,
        query_str: str,
        base_field_name: str,
    ):
        if base_field_name not in self.field_mapping:
            raise Exception()

        if "queries" not in self.field_mapping[base_field_name]:
            return MATCH_NONE

        all_queries = None
        for query_type in self.field_mapping[base_field_name]["queries"]:
            for analysis_type in self.field_mapping[base_field_name]["analysis"]:
                search_query_obj = self._get_searchquery_for_query_field_querytype_analysistype(
                    query_str,
                    base_field_name,
                    query_type,
                    analysis_type
                )
                if all_queries is None:
                    all_queries = search_query_obj
                else:
                    all_queries = all_queries | search_query_obj

        return all_queries

    def get_all_searchqueries(self, query_str: str):
        all_queries = None
        for base_field_name in self.field_mapping:
            search_query_obj = self._get_all_searchqueries_for_field(
                query_str,
                base_field_name,
            )
            if all_queries is None:
                all_queries = search_query_obj
            else:
                all_queries = all_queries | search_query_obj

        return all_queries

    def build_query(
        self,
        query: str,
        *args,
        **kwargs
    ) -> tuple[Any, Collection[Any], Dict[str, Any]]:
        """
        Allows overriding of the query structure passed to the Wagtail
        "search()" method
        """
        return query, args, kwargs


class SearchVector(QueryBuilder):

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


#
# New vectors for complex search alongside v2 - should get rolled in at end of
# the indexing improvements workstream. Need to be alongside to run v2 and v2.5
# queries side by side, e.g. for "explore" page
#


class NewAllPagesSearchVector(AllPagesSearchVector):
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
            settings.SEARCH_BOOST_VARIABLES['SEARCH_FUZZY']
        )
        # Fuzzy requires partials off
        kwargs['partial_match'] = False

        return (
            search_queries |
            fuzzy
        ), args, kwargs

    def search(self, query, *args, **kwargs):
        query, args, kwargs = self.build_query(
            query,
            *args,
            operator="and",
            **kwargs
        )
        # @TODO needs working on
        queryset = self.get_queryset()  # removed  pinning / unpinning
        return self._wagtail_search(queryset, query, *args, **kwargs)


class NewGuidanceSearchVector(GuidanceSearchVector):
    pass


class NewNewsSearchVector(NewsSearchVector):
    pass


class NewToolsSearchVector(ToolsSearchVector):
    pass


class NewPeopleSearchVector(PeopleSearchVector):
    field_mapping = {
        "full_name": {
            "boost_key": "PERSON_NAME",
            "analysis": [
                AnalysisType.TOKENIZED,
                AnalysisType.EXPLICIT,
            ],
            "queries": [
                SearchQueryType.PHRASE,
                SearchQueryType.QUERY_AND,
                SearchQueryType.QUERY_OR,
            ]
        },
        "email": {
            "boost_key": "PERSON_EMAIL_PHONE",
            "analysis": [
                AnalysisType.KEYWORD,
            ],
            "queries": [
                SearchQueryType.PHRASE,
            ]
        },
        "contact_email": {
            "boost_key": "PERSON_EMAIL_PHONE",
            "analysis": [
                AnalysisType.KEYWORD,
            ],
            "queries": [
                SearchQueryType.PHRASE,
            ]
        },
        "primary_phone_number": {
            "boost_key": "PERSON_EMAIL_PHONE",
            "analysis": [
                AnalysisType.KEYWORD,
            ],
            "queries": [
                SearchQueryType.PHRASE,
            ]
        },
        "secondary_phone_number": {
            "boost_key": "PERSON_EMAIL_PHONE",
            "analysis": [
                AnalysisType.KEYWORD,
            ],
            "queries": [
                SearchQueryType.PHRASE,
            ]
        },
        "town_city_or_region": {
            "boost_key": "PERSON_LOCATION",
            "analysis": [
                AnalysisType.TOKENIZED,
            ],
            "queries": [
                SearchQueryType.PHRASE,
                SearchQueryType.QUERY_AND,
                SearchQueryType.QUERY_OR,
            ]
        },
        "regional_building": {
            "boost_key": "PERSON_LOCATION",
            "analysis": [
                AnalysisType.TOKENIZED,
            ],
            "queries": [
                SearchQueryType.PHRASE,
                SearchQueryType.QUERY_AND,
                SearchQueryType.QUERY_OR,
            ]
        },
        "international_building": {
            "boost_key": "PERSON_LOCATION",
            "analysis": [
                AnalysisType.TOKENIZED,
            ],
            "queries": [
                SearchQueryType.PHRASE,
                SearchQueryType.QUERY_AND,
                SearchQueryType.QUERY_OR,
            ]
        },
        "fluent_languages": {
            "boost_key": "PERSON_LANGUAGES",
            "analysis": [
                AnalysisType.TOKENIZED,
            ],
            "queries": [
                SearchQueryType.PHRASE,
                SearchQueryType.QUERY_AND,
                SearchQueryType.QUERY_OR,
            ]
        },
        "search_teams": {
            "boost_key": "PERSON_TEAM",
            "analysis": [
                AnalysisType.TOKENIZED,
                AnalysisType.EXPLICIT,
            ],
            "queries": [
                SearchQueryType.PHRASE,
                SearchQueryType.QUERY_AND,
                SearchQueryType.QUERY_OR,
            ]
        },
        "profile_completion_amount": {
            "boost_key": "PERSON_PROFILE_COMPLETENESS",
            "analysis": [
                AnalysisType.PROXIMITY,
            ],
        },
        "has_photo": {
            "boost_key": "PERSON_HAS_PHOTO",
            "analysis": [
                AnalysisType.PROXIMITY,
            ],
        },
        "roles": {
            "boost_key": "PERSON_ROLE",
            "analysis": [
                AnalysisType.TOKENIZED,
                AnalysisType.EXPLICIT,
            ],
            "queries": [
                SearchQueryType.PHRASE,
                SearchQueryType.QUERY_AND,
                SearchQueryType.QUERY_OR,
            ]
        },
        "key_skills": {
            "boost_key": "PERSON_SKILLS",
            "analysis": [
                AnalysisType.TOKENIZED,
                AnalysisType.EXPLICIT,
            ],
            "queries": [
                SearchQueryType.PHRASE,
                SearchQueryType.QUERY_AND,
                SearchQueryType.QUERY_OR,
            ]
        },
        "learning_interests": {
            "boost_key": "PERSON_INTERESTS",
            "analysis": [
                AnalysisType.TOKENIZED,
            ],
            "queries": [
                SearchQueryType.PHRASE,
                SearchQueryType.QUERY_AND,
                SearchQueryType.QUERY_OR,
            ]
        },
        "additional_roles": {
            "boost_key": "PERSON_ADDITIONAL_ROLES",
            "analysis": [
                AnalysisType.TOKENIZED,
                AnalysisType.EXPLICIT,
            ],
            "queries": [
                SearchQueryType.PHRASE,
                SearchQueryType.QUERY_AND,
                SearchQueryType.QUERY_OR,
            ]
        },
        "networks": {
            "boost_key": "PERSON_NETWORKS",
            "analysis": [
                AnalysisType.TOKENIZED,
                AnalysisType.EXPLICIT,
            ],
            "queries": [
                SearchQueryType.PHRASE,
                SearchQueryType.QUERY_AND,
                SearchQueryType.QUERY_OR,
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
            settings.SEARCH_BOOST_VARIABLES['SEARCH_FUZZY']
        )
        # Fuzzy requires partials off
        kwargs['partial_match'] = False

        return (
            search_queries |
            fuzzy
        ), args, kwargs


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
            settings.SEARCH_BOOST_VARIABLES['SEARCH_FUZZY']
        )
        # Fuzzy requires partials off
        kwargs['partial_match'] = False

        return (
            search_queries |
            fuzzy
        ), args, kwargs
