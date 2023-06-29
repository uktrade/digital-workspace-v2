import logging
from django.contrib.contenttypes.models import ContentType
from django.conf import settings as dj_settings
from django.core import checks
from django.db import models
from wagtail.search.index import FilterField
from wagtail.search.query import Boost, Fuzzy, Phrase, PlainText

from search.utils import split_query
from search_extended.backends.query import OnlyFields
from search_extended.index import AutocompleteField, SearchField, RelatedFields
from search_extended.settings import search_extended_settings as settings
from search_extended.types import AnalysisType, SearchQueryType

from typing import Any, Collection, Dict

logger = logging.getLogger(__name__)


class QueryBuilder:

    @classmethod
    def _get_indexed_field_name(cls, model_field_name, analyzer):
        analyzer_settings = settings.ANALYZERS[analyzer.value]
        field_name_suffix = analyzer_settings['index_fieldname_suffix'] or ""
        return f"{model_field_name}{field_name_suffix}"

    @classmethod
    def _get_inner_searchquery_for_querytype(
        cls,
        query_str: str,
        query_type: SearchQueryType,
    ):
        query_parts = split_query(query_str)  # @TODO should really do this via wagtail parse_query_string (overridden?)
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

        # @TODO SORT THE SETTINGS STUFF OUT!!
        boost_settings = dj_settings.SEARCH_EXTENDED["BOOST_VARIABLES"]

        return (
            boost_settings[query_type_boost] *
            boost_settings[analysis_type_boost] *
            boost_settings[field_boost_key]
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
        if query is None:
            return None

        boost = cls._get_boost_for_field_querytype_analysistype(
            base_field_name,
            model_class,
            query_type,
            analysis_type
        )

        field_name = cls._get_indexed_field_name(
            base_field_name,
            analysis_type
        )
        return OnlyFields(Boost(query, boost), fields=[field_name])

    @classmethod
    def _add_to_query(cls, query, query_part):
        if query is None:
            return query_part
        return query | query_part

    @classmethod
    def _get_search_query_from_mapping(
        cls,
        query_str,
        model_class,
        field_mapping
    ):
        analyzer_settings = settings.ANALYZERS
        subquery = None
        if "related_fields" in field_mapping:
            for related_field_mapping in field_mapping["related_fields"]:
                # @TODO how to get a Nested Field query reliably?
                subquery = cls._add_to_query(
                    subquery,
                    cls._get_search_query_from_mapping(
                        query_str,
                        model_class,
                        related_field_mapping
                    )
                )

        if "search" in field_mapping:
            for analyzer in field_mapping["search"]:
                for query_type in analyzer_settings[analyzer.value]["query_types"]:
                    query_element = cls._get_searchquery_for_query_field_querytype_analysistype(
                            query_str,
                            model_class,
                            field_mapping["model_field_name"],
                            SearchQueryType(query_type),
                            analyzer,
                        )
                    if query_element is not None:
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
                query_str,
                model_class,
                field_mapping
            )
            if query_elements is not None:
                query = cls._add_to_query(
                    query,
                    query_elements,
                )

        logger.debug(query)
        return query


class ModelIndexManager(QueryBuilder):
    fields = []

    def __new__(cls, inherited_search_fields=None):
        cls.inherited_search_fields = inherited_search_fields
        return cls.get_search_fields()

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
    def _get_related_fields(cls, model_field_name, mapping):
        fields = []
        for related_field_mapping in mapping:
            fields += cls._get_search_fields_from_mapping(related_field_mapping)
        return [RelatedFields(model_field_name, fields), ]

    @classmethod
    def _get_search_fields_from_mapping(cls, field_mapping):
        if "related_fields" in field_mapping:
            return cls._get_related_fields(
                field_mapping["model_field_name"],
                field_mapping["related_fields"]
            )

        if "search" in field_mapping:
            return cls._get_searchable_search_fields(
                field_mapping["model_field_name"],
                field_mapping["search"]
            )

        if "autocomplete" in field_mapping:
            return cls._get_autocomplete_search_fields(
                field_mapping["model_field_name"],
                field_mapping["autocomplete"]
            )

        if "filter" in field_mapping:
            return cls._get_filterable_search_fields(
                field_mapping["model_field_name"],
                field_mapping["filter"]
            )

        return []

    @classmethod
    def get_mapping(self):
        mapping = []
        for field in self.fields:
            mapping += [field.mapping, ]
        return mapping

    @classmethod
    def get_search_fields(cls):
        index_fields = []
        if cls.inherited_search_fields is not None:
            index_fields = cls.inherited_search_fields

        for field_mapping in cls.get_mapping():
            index_fields += cls._get_search_fields_from_mapping(field_mapping)
        return index_fields


class AbstractBaseField:
    def __init__(
        self,
        name,
        model_field_name=None,
        **kwargs
    ):
        self.name = kwargs['name'] = name
        self.model_field_name = kwargs['model_field_name'] = model_field_name
        self.kwargs = kwargs

    def _get_base_mapping_object(self):
        return {
            "name": self.name,
            "model_field_name": self.model_field_name or self.name
        }

    def get_mapping(self):
        return self._get_base_mapping_object()

    @property
    def mapping(self):
        return self.get_mapping()


class BaseIndexedField(AbstractBaseField):
    def __init__(
        self,
        *args,
        search=False,
        autocomplete=False,
        filter=False,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.search = kwargs['search'] = search
        self.autocomplete = kwargs['autocomplete'] = autocomplete
        self.filter = kwargs['filter'] = filter
        self.kwargs = kwargs

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
        mapping = super().get_mapping()
        if self.search:
            mapping = mapping | self._get_search_mapping_object()
        if self.autocomplete:
            mapping = mapping | self._get_autocomplete_mapping_object()
        if self.filter:
            mapping = mapping | self._get_filter_mapping_object()
        return mapping


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


class RelatedIndexedFields(AbstractBaseField):
    def __init__(
        self,
        name,
        related_fields,
        *args,
        **kwargs
    ):
        super().__init__(name, *args, **kwargs)
        self.related_fields = kwargs['related_fields'] = related_fields
        self.kwargs = kwargs

    def _get_related_mapping_object(self):
        fields = []
        for field in self.related_fields:
            fields += [field.get_mapping()]
        return {
            "related_fields": fields,
        }

    def get_mapping(self):
        mapping = super().get_mapping()
        return mapping | self._get_related_mapping_object()
