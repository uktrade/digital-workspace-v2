import logging
from typing import Optional

from django.contrib.contenttypes.models import ContentType
from django.db import models
from wagtail.search.query import Boost, Fuzzy, Phrase, PlainText, SearchQuery

from extended_search.backends.query import Nested, OnlyFields, FunctionScore
from extended_search.settings import extended_search_settings as search_settings
from extended_search.types import AnalysisType, SearchQueryType

logger = logging.getLogger(__name__)


class QueryBuilder:
    @classmethod
    def _get_inner_searchquery_for_querytype(
        cls,
        query_str: str,
        query_type: SearchQueryType,
    ):
        # split can be super basic since we don't support advanced search
        query_parts = query_str.split()
        match query_type:
            case SearchQueryType.PHRASE:
                query = Phrase(query_str)
            case SearchQueryType.QUERY_AND:
                # check the query_str merits an AND - does it contain multiple words?
                if len(query_parts) > 1:
                    query = PlainText(query_str, operator="and")
                else:
                    query = None
            case SearchQueryType.QUERY_OR:
                query = PlainText(query_str, operator="or")
            case SearchQueryType.FUZZY:
                query = Fuzzy(query_str)
            case _:
                raise ValueError(f"{query_type} must be a valid SearchQueryType")
        return query

    @classmethod
    def _get_boost_for_querytype(cls, query_type: SearchQueryType):
        match query_type:
            case SearchQueryType.PHRASE:
                query_boost_key = "phrase"
            case SearchQueryType.QUERY_AND:
                query_boost_key = "query_and"
            case SearchQueryType.QUERY_OR:
                query_boost_key = "query_or"
            case SearchQueryType.FUZZY:
                query_boost_key = "fuzzy"
            case _:
                raise ValueError(f"{query_type} must be a valid SearchQueryType")

        if setting_boost := search_settings["boost_parts"]["query_types"][
            query_boost_key
        ]:
            return float(setting_boost)
        return 1.0

    @classmethod
    def _get_boost_for_analysistype(cls, analysis_type: AnalysisType):
        match analysis_type:
            case AnalysisType.EXPLICIT:
                analysis_boost_key = "explicit"
            case AnalysisType.TOKENIZED:
                analysis_boost_key = "tokenized"
            case AnalysisType.KEYWORD:
                analysis_boost_key = "explicit"
            case AnalysisType.PROXIMITY:
                analysis_boost_key = 1.0  # @TODO figure out how to add this
            case AnalysisType.FILTER:
                analysis_boost_key = 1.0  # @TODO figure out how to add this
            case _:
                raise ValueError(f"{analysis_type} must be a valid AnalysisType")
        if setting_boost := search_settings["boost_parts"]["analyzers"][
            analysis_boost_key
        ]:
            return float(setting_boost)
        return 1.0

    @classmethod
    def _get_boost_for_field(cls, model_class, field_name):
        content_type = ContentType.objects.get_for_model(model_class)
        field_boost_key = f"{content_type.app_label}.{content_type.model}.{field_name}"
        if setting_boost := search_settings["boost_parts"]["fields"][field_boost_key]:
            return float(setting_boost)
        return 1.0

    @classmethod
    def _get_boost_for_field_querytype_analysistype(
        cls,
        field_name: str,
        model_class: models.Model,
        query_type: SearchQueryType,
        analysis_type: AnalysisType,
    ):
        query_boost = cls._get_boost_for_querytype(query_type)
        analyzer_boost = cls._get_boost_for_analysistype(analysis_type)
        field_boost = cls._get_boost_for_field(
            model_class,
            field_name,
        )

        return query_boost * analyzer_boost * field_boost

    @classmethod
    def _get_searchquery_for_query_field_querytype_analysistype(
        cls,
        query_str: str,
        model_class: models.Model,
        base_field_name: str,
        query_type: SearchQueryType,
        analysis_type: AnalysisType,
        field_mapping: dict,
    ):
        query = cls._get_inner_searchquery_for_querytype(
            query_str,
            query_type,
        )
        if query is None:
            return None

        boost = cls._get_boost_for_field_querytype_analysistype(
            base_field_name,
            model_class,
            query_type,
            analysis_type,
        )

        return OnlyFields(Boost(query, boost), fields=[base_field_name])

    @classmethod
    def _combine_queries(cls, q1: Optional[SearchQuery], q2: Optional[SearchQuery]):
        if q1 and q2:
            return q1 | q2
        return q1 or q2

    @classmethod
    def _get_search_query_from_mapping(cls, query_str, model_class, field_mapping):
        print(">>", field_mapping)
        subquery = None

        if "search" in field_mapping:
            for analyzer in field_mapping["search"]:
                for query_type in search_settings[
                    f"analyzers__{analyzer.value}__query_types"
                ]:
                    query_element = (
                        cls._get_searchquery_for_query_field_querytype_analysistype(
                            query_str,
                            model_class,
                            field_mapping["model_field_name"],
                            SearchQueryType(query_type),
                            analyzer,
                            field_mapping,
                        )
                    )
                    if query_element is not None and "function_score" in field_mapping:
                        params = [
                            (k, v)
                            for k, v in field_mapping["function_score"][
                                "function_params"
                            ].items()
                        ]
                        query_element = FunctionScore(
                            query_element,
                            field=f"{query_element.fields[0]}_keyword",
                            function_name=field_mapping["function_score"][
                                "function_name"
                            ],
                            function_params=params,
                        )
                    subquery = cls._combine_queries(
                        subquery,
                        query_element,
                    )

        if "fuzzy" in field_mapping:
            query_element = cls._get_searchquery_for_query_field_querytype_analysistype(
                query_str,
                model_class,
                field_mapping["model_field_name"],
                SearchQueryType("fuzzy"),
                AnalysisType("tokenized"),
                field_mapping,
            )
            subquery = cls._combine_queries(
                subquery,
                query_element,
            )

        return subquery


class NestedQueryBuilder(QueryBuilder):
    @classmethod
    def _get_searchquery_for_query_field_querytype_analysistype(
        cls,
        query_str: str,
        model_class: models.Model,
        base_field_name: str,
        query_type: SearchQueryType,
        analysis_type: AnalysisType,
        field_mapping: dict,
    ):
        # @TODO: Come up with a better name for this, and/or move it higher up
        field_name = base_field_name
        if pmf := field_mapping.get("parent_model_field"):
            field_name = f"{pmf}.{field_name}"

        return super()._get_searchquery_for_query_field_querytype_analysistype(
            query_str,
            model_class,
            field_name,
            query_type,
            analysis_type,
            field_mapping,
        )

    @classmethod
    def _get_search_query_from_mapping(cls, query_str, model_class, field_mapping):
        subquery = super()._get_search_query_from_mapping(
            query_str, model_class, field_mapping
        )
        if "related_fields" not in field_mapping:
            return subquery

        internal_subquery = None
        for related_field_mapping in field_mapping["related_fields"]:
            internal_subquery = cls._combine_queries(
                internal_subquery,
                cls._get_search_query_from_mapping(
                    query_str, model_class, related_field_mapping
                ),
            )
        nested_subquery = Nested(
            subquery=internal_subquery, path=field_mapping["model_field_name"]
        )

        return cls._combine_queries(
            nested_subquery,
            subquery,
        )
