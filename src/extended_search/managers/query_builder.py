import logging
from django.db import models
from wagtail.search.query import Boost, Phrase, PlainText

from search.utils import split_query
from extended_search.backends.query import OnlyFields
from extended_search.settings import DEFAULTS as settings
from extended_search.types import AnalysisType, SearchQueryType


logger = logging.getLogger(__name__)


class QueryBuilder:
    @classmethod
    def _get_indexed_field_name(cls, model_field_name, analyzer):
        analyzer_settings = settings["ANALYZERS"][analyzer.value]
        field_name_suffix = analyzer_settings["index_fieldname_suffix"] or ""
        return f"{model_field_name}{field_name_suffix}"

    @classmethod
    def _get_inner_searchquery_for_querytype(
        cls,
        query_str: str,
        query_type: SearchQueryType,
    ):
        query_parts = split_query(
            query_str
        )  # @TODO should really do this via wagtail parse_query_string (overridden?)
        match query_type:
            case SearchQueryType.PHRASE:
                query = Phrase(query_str)
            case SearchQueryType.QUERY_AND:
                # @TODO check the query_str merits an AND - does it contain multiple words?
                if len(query_parts) > 1:
                    query = PlainText(query_str, operator="and")
                else:
                    query = None
            case SearchQueryType.QUERY_OR:
                query = PlainText(query_str, operator="or")
            case _:
                raise ValueError(f"{query_type} must be a valid SearchQueryType")
        return query

    @classmethod
    def _get_boost_for_field_querytype_analysistype(
        cls,
        base_field_name: str,
        model_class: models.Model,
        query_type: SearchQueryType,
        analysis_type: AnalysisType,
        field_boost: float,
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

        # content_type = ContentType.objects.get_for_model(model_class)
        # field_boost_key = (
        #     f"{content_type.app_label}.{content_type.model}.{base_field_name}"
        # )

        # @TODO SORT THE SETTINGS STUFF OUT!!
        boost_settings = settings["BOOST_VARIABLES"]

        return (
            boost_settings[query_type_boost]
            * boost_settings[analysis_type_boost]
            * field_boost  # @TODO this too!
        )

    @classmethod
    def _get_searchquery_for_query_field_querytype_analysistype(
        cls,
        query_str: str,
        model_class: models.Model,
        base_field_name: str,
        query_type: SearchQueryType,
        analysis_type: AnalysisType,
        field_boost: float,
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
            field_boost,
        )

        field_name = cls._get_indexed_field_name(base_field_name, analysis_type)
        return OnlyFields(Boost(query, boost), fields=[field_name])

    @classmethod
    def _add_to_query(cls, query, query_part):
        if query_part is None:
            return query  # even if this is _also_ None

        if query is None:
            return query_part  # the first node becomes the root

        return query | query_part

    @classmethod
    def _get_search_query_from_mapping(cls, query_str, model_class, field_mapping):
        analyzer_settings = settings["ANALYZERS"]
        subquery = None
        if "related_fields" in field_mapping:
            for related_field_mapping in field_mapping["related_fields"]:
                # @TODO how to get a Nested Field query reliably?
                subquery = cls._add_to_query(
                    subquery,
                    cls._get_search_query_from_mapping(
                        query_str, model_class, related_field_mapping
                    ),
                )

        if "search" in field_mapping:
            for analyzer in field_mapping["search"]:
                for query_type in analyzer_settings[analyzer.value]["query_types"]:
                    query_element = (
                        cls._get_searchquery_for_query_field_querytype_analysistype(
                            query_str,
                            model_class,
                            field_mapping["model_field_name"],
                            SearchQueryType(query_type),
                            analyzer,
                            field_mapping["boost"],
                        )
                    )
                    subquery = cls._add_to_query(
                        subquery,
                        query_element,
                    )

        if "autocomplete" in field_mapping:
            # @TODO sort this out!
            subquery = None

        if "filter" in field_mapping:
            # @TODO sort this out!
            subquery = None

        return subquery

    @classmethod
    def get_search_query(cls, query_str, model_class, *args, **kwargs):
        """
        Uses the field mapping to derive the full nested SearchQuery
        """
        query = None
        for field_mapping in cls.get_mapping():
            query_elements = cls._get_search_query_from_mapping(
                query_str, model_class, field_mapping
            )
            if query_elements is not None:
                query = cls._add_to_query(
                    query,
                    query_elements,
                )

        logger.debug(query)
        return query