from django.contrib.contenttypes.models import ContentType
from django.db import models
from wagtail.search import index
from wagtail.search.query import Boost, Fuzzy, Phrase, PlainText, MATCH_NONE

from search_extended.backends.query import OnlyFields
from search_extended.settings import search_extended_settings
from search_extended.types import AnalysisType, SearchQueryType

from typing import Any, Collection, Dict


class MetaIndexedExtended(type(models.Model)):

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
                raise ValueError(f"{query_type} must be a valid SearchQueryType")
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
                raise ValueError(f"{query_type} must be a valid SearchQueryType")

        match analysis_type:
            case AnalysisType.EXPLICIT:
                analysis_type_boost = "ANALYZER_EXPLICIT"
            case AnalysisType.TOKENIZED:
                analysis_type_boost = "ANALYZER_TOKENIZED"
            case AnalysisType.KEYWORD:
                analysis_type_boost = "ANALYZER_EXPLICIT"
            case AnalysisType.PROXIMITY:
                analysis_type_boost = 1.0  # @TODO figure out how to add this
            case AnalysisType.FILTER:
                analysis_type_boost = 1.0  # @TODO figure out how to add this
            case _:
                raise ValueError(f"{analysis_type} must be a valid AnalysisType")

        content_type = ContentType.objects.get_for_model(self)
        field_boost_key = f"{content_type.app_label}.{content_type.model}.{base_field_name}"

        return (
            search_extended_settings.get_boost_value(query_type_boost) *
            search_extended_settings.get_boost_value(analysis_type_boost) *
            search_extended_settings.get_boost_value(field_boost_key)
        )

    def _get_searchquery_for_query_field_querytype_analysistype(
        self,
        query_str: str,
        base_field_name: str,
        query_type: SearchQueryType,
        analysis_type: AnalysisType,
    ):
        if analysis_type in (AnalysisType.FILTER, AnalysisType.PROXIMITY,):
            return MATCH_NONE

        query = self._get_inner_searchquery_for_querytype(
            query_str,
            query_type,
        )

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
        if base_field_name not in self.search_field_mapping:
            raise KeyError(f"{base_field_name} not found in self.search_field_mapping")

        if "queries" not in self.search_field_mapping[base_field_name]:
            return MATCH_NONE

        all_queries = None
        for query_type in self.search_field_mapping[base_field_name]["queries"]:
            for analysis_type in self.search_field_mapping[base_field_name]["analysis"]:

                if analysis_type not in (AnalysisType.FILTER, AnalysisType.PROXIMITY,):

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
        for base_field_name in self.search_field_mapping:
            search_query_obj = self._get_all_searchqueries_for_field(
                query_str,
                base_field_name,
            )
            if all_queries is None:
                all_queries = search_query_obj
            else:
                all_queries = all_queries | search_query_obj

        return all_queries

    @property
    def search_fields(cls, *args, **kwargs):
        index_fields = []
        for field_name, field_mapping in cls.search_field_mapping.items():
            if 'analysis' not in field_mapping:
                index_fields += [index.SearchField(field_name)]

            for field_type in field_mapping['analysis']:
                if field_type == AnalysisType.FILTER:
                    index_fields += [index.FilterField(field_name)]
                else:
                    analyzer_settings = search_extended_settings.ANALYZERS[field_type.value]
                    field_name_suffix = analyzer_settings['index_fieldname_suffix'] or ""

                    index_fields += [
                        index.SearchField(
                            f"{field_name}{field_name_suffix}",
                            es_extra={
                                "search_analyzer": analyzer_settings['es_analyzer'],
                            },
                        )
                    ]

        return index_fields


class IndexedExtended(metaclass=MetaIndexedExtended):
    search_field_mapping = None

    def __init__(self, *args, **kwargs):
        self.search_field_mapping = kwargs.pop('search_field_mapping', None)

        if self.search_field_mapping is None:
            self.search_field_mapping = {}

        return super().__init__(*args, **kwargs)
