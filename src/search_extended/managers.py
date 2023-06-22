import logging
from django.contrib.contenttypes.models import ContentType
from django.core import checks
from django.db import models
from wagtail.search.index import FilterField, RelatedFields
from wagtail.search.query import Boost, Fuzzy, Phrase, PlainText, MATCH_NONE

from search_extended.backends.query import OnlyFields
from search_extended.index import AutocompleteField, SearchField
from search_extended.settings import search_extended_settings as settings
from search_extended.types import AnalysisType, SearchQueryType

from typing import Any, Collection, Dict

logger = logging.getLogger(__name__)


class QueryBuilder:
    @classmethod
    def _get_inner_searchquery_for_querytype(
        cls,
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

    @classmethod
    def _get_boost_for_field_querytype_analysistype(
        cls,
        base_field_name: str,
        model_class: models.Model,
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

        content_type = ContentType.objects.get_for_model(model_class)
        field_boost_key = f"{content_type.app_label}.{content_type.model}.{base_field_name}"

        return (
            settings.get_boost_value(query_type_boost) *
            settings.get_boost_value(analysis_type_boost) *
            settings.get_boost_value(field_boost_key)
        )

    @classmethod
    def _get_searchquery_for_query_field_querytype_analysistype(
        cls,
        query_str: str,
        model_class: models.Model,
        base_field_name: str,
        query_type: SearchQueryType,
        analysis_type: AnalysisType,
    ):
        query = cls._get_inner_searchquery_for_querytype(
            query_str,
            query_type,
        )

        boost = cls._get_boost_for_field_querytype_analysistype(base_field_name, model_class, query_type, analysis_type)

        field_name = base_field_name
        return OnlyFields(Boost(query, boost), fields=[field_name])

    @classmethod
    def get_search_query(cls, query_str, model_class, *args, **kwargs):
        """
        Uses the field mapping to derive the full nested SearchQuery
        """
        query = None
        analyzer_settings = settings.ANALYZERS
        for field_mapping in cls.get_mapping():
            # @TODO - RelatedFields!
            if "search" in field_mapping:
                for analyzer in field_mapping["search"]:
                    for query_type in analyzer_settings[analyzer.value]["query_types"]:
                        query_part = cls._get_searchquery_for_query_field_querytype_analysistype(
                            query_str,
                            model_class,
                            field_mapping["model_field_name"],
                            SearchQueryType(query_type),
                            analyzer,
                        )
                        if query is None:
                            query = query_part
                        else:
                            query = query | query_part

            if "autocomplete" in field_mapping:
                query_part = cls._get_autocomplete_search_fields(field_mapping["model_field_name"], field_mapping["autocomplete"])

            if "filter" in field_mapping:
                query_part = cls._get_filterable_search_fields(field_mapping["model_field_name"], field_mapping["filter"])

        logger.debug(query)
        return query



class ModelIndexManager(QueryBuilder):
    fields = []

    def __new__(cls):
        return cls.get_search_fields()

    @classmethod
    def _get_indexed_field_name(cls, model_field_name, analyzer):
        analyzer_settings = settings.ANALYZERS[analyzer.value]
        field_name_suffix = analyzer_settings['index_fieldname_suffix'] or ""
        return f"{model_field_name}{field_name_suffix}"

    @classmethod
    def _get_analyzer_name(cls, analyzer_type):
        analyzer_settings = settings.ANALYZERS[analyzer_type.value]
        return analyzer_settings['es_analyzer']

    @classmethod
    def _get_searchable_search_fields(cls, model_field_name, analyzers):
        fields = []
        if len(analyzers) == 0:
            analyzers = [AnalysisType.TOKENIZED]

        for analyzer in analyzers:
            index_field_name = cls._get_indexed_field_name(model_field_name, analyzer)
            field = SearchField(
                index_field_name,
                model_field_name=model_field_name,
                es_extra={"search_analyzer": cls._get_analyzer_name(analyzer),}
            )
            fields += [field, ]
        return fields

    @classmethod
    def _get_autocomplete_search_fields(cls, model_field_name, analyzers):
        fields = []
        if len(analyzers) == 0:
            analyzers = [AnalysisType.TOKENIZED]

        for analyzer in analyzers:
            index_field_name = cls._get_indexed_field_name(model_field_name, analyzer)
            field = AutocompleteField(
                index_field_name,
                model_field_name=model_field_name,
                es_extra={"search_analyzer": cls._get_analyzer_name(analyzer),}
            )
            fields += [field, ]
        return fields

    @classmethod
    def _get_filterable_search_fields(cls, model_field_name, analyzers):
        return [FilterField(model_field_name), ]

    @classmethod
    def get_mapping(self):
        mapping = []
        for field in self.fields:
            mapping += [field.mapping, ]
        return mapping

    @classmethod
    def get_search_fields(cls):
        index_fields = []
        for field_mapping in cls.get_mapping():
            # @TODO - RelatedFields!
            if "search" in field_mapping:
                index_fields += cls._get_searchable_search_fields(field_mapping["model_field_name"], field_mapping["search"])

            if "autocomplete" in field_mapping:
                index_fields += cls._get_autocomplete_search_fields(field_mapping["model_field_name"], field_mapping["autocomplete"])

            if "filter" in field_mapping:
                index_fields += cls._get_filterable_search_fields(field_mapping["model_field_name"], field_mapping["filter"])
        return index_fields


class BaseIndexedField:
    def __init__(
        self,
        name,
        search=False,
        autocomplete=False,
        filter=False,
        model_field_name=None,
        **kwargs
    ):
        self.name = kwargs['name'] = name
        self.model_field_name = kwargs['model_field_name'] = model_field_name
        self.search = kwargs['search'] = search
        self.autocomplete = kwargs['autocomplete'] = autocomplete
        self.filter = kwargs['filter'] = filter
        self.kwargs = kwargs

    def _get_base_mapping_object(self):
        return {
            "name": self.name,
            "model_field_name": self.model_field_name or self.name
        }

    def _get_search_mapping_object(self):
        return {
            "search": None
        }

    def _get_autocomplete_mapping_object(self):
        return {
            "autocomplete": None
        }

    def _get_filter_mapping_object(self):
        return {
            "filter": None
        }

    def get_mapping(self):
        mapping = self._get_base_mapping_object()
        if self.search:
            mapping = mapping | self._get_search_mapping_object()
        if self.autocomplete:
            mapping = mapping | self._get_autocomplete_mapping_object()
        if self.filter:
            mapping = mapping | self._get_filter_mapping_object()
        return mapping

    @property
    def mapping(self):
        return self.get_mapping()


class IndexedField(BaseIndexedField):
    def __init__(
        self,
        *args,
        tokenized=False,
        explicit=False,
        keyword=False,
        proximity=False,  # @TODO How to implement this?
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.tokenized = kwargs['tokenized'] = tokenized
        self.explicit = kwargs['explicit'] = explicit
        self.keyword = kwargs['keyword'] = keyword
        self.proximity = kwargs['proximity'] = proximity

        if tokenized or explicit or keyword:
            self.search = True

    def _get_search_mapping_object(self):
        mapping = {
            "search": []
        }
        if self.tokenized:
            mapping["search"] += [AnalysisType.TOKENIZED]
        if self.explicit:
            mapping["search"] += [AnalysisType.EXPLICIT]
        if self.keyword:
            mapping["search"] += [AnalysisType.KEYWORD]
        if self.proximity:
            mapping["search"] += [AnalysisType.PROXIMITY]
        return mapping
