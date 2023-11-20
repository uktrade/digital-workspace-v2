import inspect
import logging
from typing import Optional

from django.core.cache import cache
from django.db import models
from wagtail.search import index
from wagtail.search.query import Boost, Fuzzy, Phrase, PlainText, SearchQuery

from extended_search.backends.query import Filtered, Nested, OnlyFields
from extended_search.index import (
    BaseField,
    IndexedField,
    RelatedFields,
    SearchField,
    get_indexed_models,
)
from extended_search.settings import extended_search_settings as search_settings
from extended_search.settings import get_settings_field_key
from extended_search.types import AnalysisType, SearchQueryType

logger = logging.getLogger(__name__)


class Variable:
    def __init__(self, name: str, query_type: SearchQueryType) -> None:
        self.name = name
        self.query_type = query_type

    def output(self, query_str: str):
        # split can be super basic since we don't support advanced search
        query_parts = query_str.split()
        match self.query_type:
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
                raise ValueError(f"{self.query_type} must be a valid SearchQueryType")
        return query


class QueryBuilder:
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
        definition_class = field.get_definition_model(model_class)
        field_key = get_settings_field_key(definition_class, field)
        if setting_boost := search_settings["boost_parts"]["fields"][field_key]:
            return float(setting_boost)
        return 1.0

    @classmethod
    def _get_boost_for_field_querytype_analysistype(
        cls,
        model_class: models.Model,
        query_type: SearchQueryType,
        analysis_type: AnalysisType,
        field: index.BaseField,
    ):
        query_boost = cls._get_boost_for_querytype(query_type)
        analyzer_boost = cls._get_boost_for_analysistype(analysis_type)
        field_boost = cls._get_boost_for_field(
            model_class,
            field,
        )

        return query_boost * analyzer_boost * field_boost

    @classmethod
    def _build_searchquery_for_query_field_querytype_analysistype(
        cls,
        model_class: models.Model,
        base_field_name: str,
        query_type: SearchQueryType,
        analysis_type: AnalysisType,
        field: index.BaseField,
    ):
        from extended_search.managers import get_indexed_field_name

        if isinstance(field, BaseField):
            base_field_name = field.get_full_model_field_name()

        boost = cls._get_boost_for_field_querytype_analysistype(
            model_class,
            query_type,
            analysis_type,
            field,
        )

        field_name = get_indexed_field_name(base_field_name, analysis_type)
        return OnlyFields(
            Boost(Variable("search_query", query_type), boost), fields=[field_name]
        )

    @classmethod
    def _combine_queries(cls, q1: Optional[SearchQuery], q2: Optional[SearchQuery]):
        if q1 and q2:
            return q1 | q2
        return q1 or q2

    @classmethod
    def _build_search_query_for_searchfield(
        cls, field, model_class, subquery, analyzer
    ):
        for query_type in search_settings["analyzers"][analyzer.value]["query_types"]:
            query_element = (
                cls._build_searchquery_for_query_field_querytype_analysistype(
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
        return subquery

    @classmethod
    def _build_search_query_for_indexfield(cls, field, model_class, subquery):
        if not field.search:
            return subquery

        for analyzer in field.get_search_analyzers():
            subquery = cls._build_search_query_for_searchfield(
                field, model_class, subquery, analyzer
            )

        if field.fuzzy:
            query_element = (
                cls._build_searchquery_for_query_field_querytype_analysistype(
                    model_class,
                    field.model_field_name,
                    SearchQueryType("fuzzy"),
                    AnalysisType.TOKENIZED,
                    field,
                )
            )
            subquery = cls._combine_queries(
                subquery,
                query_element,
            )

        return subquery

    @classmethod
    def _build_search_query(
        cls,
        model_class: models.Model,
        field: index.BaseField,
    ):
        # @TODO verify this works if not everything is an IndexedField
        subquery = None

        if isinstance(field, IndexedField):
            subquery = cls._build_search_query_for_indexfield(
                field, model_class, subquery
            )

        elif isinstance(field, RelatedFields):
            internal_subquery = None
            for related_field in field.fields:
                internal_subquery = cls._combine_queries(
                    internal_subquery,
                    cls._build_search_query(model_class, related_field),
                )
            subquery = cls._combine_queries(
                Nested(subquery=internal_subquery, path=field.model_field_name),
                subquery,
            )

        elif isinstance(field, SearchField):
            subquery = cls._build_search_query_for_searchfield(
                field,
                model_class,
                subquery,
                cls.infer_analyzer_from_field(field),
            )

        return subquery

    @classmethod
    def infer_analyzer_from_field(cls, field: index.BaseField):
        # @TODO 😭
        if "es_extra" not in field.kwargs:
            return AnalysisType.TOKENIZED

        es_analyzer = field.kwargs["es_extra"].get("es_analyzer")
        if not es_analyzer:
            return AnalysisType.TOKENIZED

        analyzer_settings = search_settings["analyzers"]
        for analyzer_name, analyzer_setting in analyzer_settings.items():
            if analyzer_setting["es_analyzer"] == es_analyzer:
                return AnalysisType(analyzer_name)

        return AnalysisType.TOKENIZED


class CustomQueryBuilder(QueryBuilder):
    @classmethod
    def build_query_for_model(cls, model_class) -> Optional[SearchQuery]:
        query = None
        for (
            field
        ) in (
            model_class.get_all_indexed_fields_including_from_parents_and_refactor_this()
        ):
            query_elements = cls._build_search_query(model_class, field)
            if query_elements is not None:
                query = cls._combine_queries(
                    query,
                    query_elements,
                )
        return query

    @classmethod
    def swap_variables(
        cls, query: SearchQuery, search_query: str
    ) -> Optional[SearchQuery]:
        """
        Iterate through the query and swap out variables for the search_query.
        """

        if isinstance(query, Variable):
            return query.output(search_query)

        if hasattr(query, "subqueries"):
            query.subqueries = [
                cls.swap_variables(sq, search_query) for sq in query.subqueries
            ]
            query.subqueries = [sq for sq in query.subqueries if sq]

            if not query.subqueries:
                return None
            elif len(query.subqueries) == 1:
                return query.subqueries[0]

        if hasattr(query, "subquery"):
            query.subquery = cls.swap_variables(query.subquery, search_query)
            if not query.subquery:
                return None

        return query

    @classmethod
    def get_search_query(cls, model_class, query_str: str):
        cache_key = model_class.__name__
        built_query = cache.get(cache_key, None)
        if not built_query:
            built_query = cls.build_search_query(model_class)
            cache.set(cache_key, built_query, 60 * 60)
        return cls.swap_variables(built_query, query_str)

    @classmethod
    def build_search_query(cls, model_class):
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

            subquery = cls.build_query_for_model(sub_model_class)
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
        subquery = cls.build_query_for_model(model_class)
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
