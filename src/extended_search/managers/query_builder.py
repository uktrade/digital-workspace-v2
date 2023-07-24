import logging
from django.contrib.contenttypes.models import ContentType
from django.db import models
from wagtail.search.query import Boost, Phrase, PlainText

from search.utils import split_query
from extended_search.backends.query import OnlyFields
from extended_search.settings import extended_search_settings as search_settings
from extended_search.types import AnalysisType, SearchQueryType


logger = logging.getLogger(__name__)


class QueryBuilder:
    @classmethod
    def _get_indexed_field_name(cls, model_field_name, analyzer):
        field_name_suffix = (
            search_settings[f"analyzers__{analyzer.value}__index_fieldname_suffix"]
            or ""
        )
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
        field_mapping: dict,
    ):
        match query_type:
            case SearchQueryType.PHRASE:
                query_type_boost = "phrase"
            case SearchQueryType.QUERY_AND:
                query_type_boost = "query_and"
            case SearchQueryType.QUERY_OR:
                query_type_boost = "query_or"
            case SearchQueryType.FUZZY:
                query_type_boost = "fuzzy"
            case _:
                raise ValueError(f"{query_type} must be a valid SearchQueryType")

        match analysis_type:
            case AnalysisType.EXPLICIT:
                analysis_type_boost = "explicit"
            case AnalysisType.TOKENIZED:
                analysis_type_boost = "tokenized"
            case AnalysisType.KEYWORD:
                analysis_type_boost = "explicit"
            case AnalysisType.PROXIMITY:
                analysis_type_boost = 1.0  # @TODO figure out how to add this
            case AnalysisType.FILTER:
                analysis_type_boost = 1.0  # @TODO figure out how to add this
            case _:
                raise ValueError(f"{analysis_type} must be a valid AnalysisType")

        content_type = ContentType.objects.get_for_model(model_class)
        field_name = base_field_name  # cls._get_indexed_field_name(base_field_name, analysis_type)
        if "related_field" in field_mapping:
            field_name = f"{field_mapping['related_field']}.{field_name}"
        field_boost_key = f"{content_type.app_label}.{content_type.model}.{field_name}"

        return (
            float(search_settings[f"boost_parts__query_types__{query_type_boost}"])
            * float(search_settings[f"boost_parts__analyzers__{analysis_type_boost}"])
            * float(search_settings[f"boost_parts__fields__{field_boost_key}"])
        )

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
            field_mapping,
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
        subquery = None
        if "related_fields" in field_mapping:
            for related_field_mapping in field_mapping["related_fields"]:
                # # @TODO how to get a Nested Field query reliably?
                related_field_mapping["related_field"] = field_mapping["name"]
                # related_field_mapping[
                #     "name"
                # ] = f"{field_mapping['name']}.{related_field_mapping['name']}"

                subquery = cls._add_to_query(
                    subquery,
                    cls._get_search_query_from_mapping(
                        query_str, model_class, related_field_mapping
                    ),
                )

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
