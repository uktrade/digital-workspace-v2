import inspect
import logging
from typing import Optional

from django.contrib.contenttypes.models import ContentType
from django.db import models
from extended_search.backends.query import Filtered, Nested, OnlyFields
from extended_search.index import (
    IndexedField,
    RelatedFields,
    get_indexed_models,
)
from extended_search.settings import extended_search_settings as search_settings
from extended_search.types import AnalysisType, SearchQueryType
from wagtail.search.index import BaseField
from wagtail.search.query import Boost, Fuzzy, Phrase, PlainText, SearchQuery


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
    def _get_boost_for_field(cls, model_class, field):
        definition_cls = field.get_definition_model(model_class)
        content_type = ContentType.objects.get_for_model(definition_cls)

        field_boost_key = (
            f"{content_type.app_label}.{content_type.model}.{field.field_name}"
        )
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
        field: BaseField,
    ):
        query_boost = cls._get_boost_for_querytype(query_type)
        analyzer_boost = cls._get_boost_for_analysistype(analysis_type)
        field_boost = cls._get_boost_for_field(
            model_class,
            field,
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
        field: BaseField,
    ):
        from extended_search.managers import get_indexed_field_name

        field_name = base_field_name
        # if pmf := field_mapping.get("parent_model_field"):
        #     field_name = f"{pmf}.{field_name}"
        # @TODO parent!

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
            field,
        )

        field_name = get_indexed_field_name(base_field_name, analysis_type)
        return OnlyFields(Boost(query, boost), fields=[field_name])

    @classmethod
    def _combine_queries(cls, q1: Optional[SearchQuery], q2: Optional[SearchQuery]):
        if q1 and q2:
            return q1 | q2
        return q1 or q2

    @classmethod
    def _get_search_query_for_searchfield(cls, field, query_str, model_class, subquery):
        for analyzer in field.get_analyzers():
            for query_type in search_settings[
                f"analyzers__{analyzer.value}__query_types"
            ]:
                query_element = (
                    cls._get_searchquery_for_query_field_querytype_analysistype(
                        query_str,
                        model_class,
                        field.model_field_name,
                        SearchQueryType(query_type),
                        analyzer,
                        field,
                    )
                )
                subquery = cls._combine_queries(
                    subquery,
                    query_element,
                )

        if field.fuzzy:
            query_element = cls._get_searchquery_for_query_field_querytype_analysistype(
                query_str,
                model_class,
                field.model_field_name,
                SearchQueryType("fuzzy"),
                AnalysisType.TOKENIZED,
                field,
            )
            subquery = cls._combine_queries(
                subquery,
                query_element,
            )

        return subquery

    @classmethod
    def _get_search_query(
        cls,
        query_str: str,
        model_class: models.Model,
        field: BaseField,
    ):
        # @TODO verify this works if not everything is an IndexedField
        subquery = None

        if isinstance(field, IndexedField):
            if field.search:
                subquery = cls._get_search_query_for_searchfield(
                    field, query_str, model_class, subquery
                )

        if isinstance(field, RelatedFields):
            internal_subquery = None
            for related_field in field.fields:
                internal_subquery = cls._combine_queries(
                    internal_subquery,
                    cls._get_search_query(query_str, model_class, related_field),
                )
            subquery = cls._combine_queries(
                Nested(subquery=internal_subquery, path=field.model_field_name),
                subquery,
            )

        return subquery


class CustomQueryBuilder(QueryBuilder):
    @classmethod
    def get_query_for_model(cls, model_class, query_str) -> Optional[SearchQuery]:
        query = None
        for (
            field
        ) in (
            model_class.get_all_indexed_fields_including_from_parents_and_refactor_this()
        ):
            query_elements = cls._get_search_query(query_str, model_class, field)
            if query_elements is not None:
                query = cls._combine_queries(
                    query,
                    query_elements,
                )
        return query

    @classmethod
    def get_search_query(cls, model_class, query_str, *args, **kwargs):
        """
        Generates a full query for a model class, by running query builder
        against the given model as well as all models with the given as a
        parent; each has it's own subquery using its own settings filtered by
        type, and all are joined together at the end.
        """
        extended_models = cls.get_extended_models_with_unique_indexed_fields(
            model_class
        )
        # build full query for each extended model
        queries = []
        queried_content_types = []
        for sub_model_class in extended_models:
            # filter so it only applies to "docs with that model anywhere in the contenttypes list"

            sub_model_contenttype = (
                f"{sub_model_class._meta.app_label}.{sub_model_class.__name__}"
            )

            subquery = cls.get_query_for_model(sub_model_class, query_str)
            query = Filtered(
                subquery=subquery,
                filters=[
                    (
                        "content_type",
                        "contains",
                        sub_model_contenttype,
                    ),
                ],
            )
            queries.append(query)
            queried_content_types.append(sub_model_contenttype)

        # build query for root model passed in to method, filter to exclude docs with contenttypes
        # matching any of the extended-models-with-dedicated-IM
        subquery = cls.get_query_for_model(model_class, query_str)
        root_query = Filtered(
            subquery=subquery,
            filters=[
                (
                    "content_type",
                    "excludes",
                    queried_content_types,
                ),
            ],
        )

        for q in queries:
            root_query |= q

        logger.debug(root_query)
        return root_query

    @classmethod
    def get_extended_models_with_unique_indexed_fields(cls, model_class):
        # iterate indexed models extending the root model that have a dedicated IndexManager
        extended_model_classes = []
        for indexed_model in get_indexed_models():
            if (
                indexed_model != model_class
                and model_class in inspect.getmro(indexed_model)
                # and indexed_model.has_indexmanager_direct_inner_class()
            ):
                extended_model_classes.append(indexed_model)
        return extended_model_classes
