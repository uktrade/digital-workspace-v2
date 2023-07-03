import logging

from wagtail.search.index import FilterField

from extended_search.index import AutocompleteField, SearchField, RelatedFields
from extended_search.managers.query_builder import QueryBuilder
from extended_search.settings import extended_search_settings as settings
from extended_search.types import AnalysisType


logger = logging.getLogger(__name__)


class ModelIndexManager(QueryBuilder):
    fields = []

    def __new__(cls, inherited_search_fields=None):
        cls.inherited_search_fields = inherited_search_fields
        return cls.get_search_fields()

    @classmethod
    def _get_analyzer_name(cls, analyzer_type):
        analyzer_settings = settings.ANALYZERS[analyzer_type.value]
        return analyzer_settings["es_analyzer"]

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
                es_extra={
                    "search_analyzer": cls._get_analyzer_name(analyzer),
                },
            )
            fields += [
                field,
            ]
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
                es_extra={
                    "search_analyzer": cls._get_analyzer_name(analyzer),
                },
            )
            fields += [
                field,
            ]
        return fields

    @classmethod
    def _get_filterable_search_fields(cls, model_field_name, analyzers):
        return [
            FilterField(model_field_name),
        ]

    @classmethod
    def _get_related_fields(cls, model_field_name, mapping):
        fields = []
        for related_field_mapping in mapping:
            fields += cls._get_search_fields_from_mapping(related_field_mapping)
        return [
            RelatedFields(model_field_name, fields),
        ]

    @classmethod
    def _get_search_fields_from_mapping(cls, field_mapping):
        if "related_fields" in field_mapping:
            return cls._get_related_fields(
                field_mapping["model_field_name"], field_mapping["related_fields"]
            )

        if "search" in field_mapping:
            return cls._get_searchable_search_fields(
                field_mapping["model_field_name"], field_mapping["search"]
            )

        if "autocomplete" in field_mapping:
            return cls._get_autocomplete_search_fields(
                field_mapping["model_field_name"], field_mapping["autocomplete"]
            )

        if "filter" in field_mapping:
            return cls._get_filterable_search_fields(
                field_mapping["model_field_name"], field_mapping["filter"]
            )

        return []

    @classmethod
    def get_mapping(self):
        mapping = []
        for field in self.fields:
            mapping += [
                field.mapping,
            ]
        return mapping

    @classmethod
    def get_search_fields(cls):
        index_fields = []
        if cls.inherited_search_fields is not None:
            index_fields = cls.inherited_search_fields

        for field_mapping in cls.get_mapping():
            index_fields += cls._get_search_fields_from_mapping(field_mapping)
        return index_fields
