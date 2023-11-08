import logging

from wagtail.search.index import FilterField

from extended_search.index import AutocompleteField, RelatedFields, SearchField
from extended_search.managers import get_indexed_field_name
from extended_search.managers.query_builder import NestedQueryBuilder
from extended_search.settings import extended_search_settings as search_settings
from extended_search.types import AnalysisType

logger = logging.getLogger(__name__)


class ModelIndexManager(NestedQueryBuilder):
    fields = []

    def __init__(self, model_class):
        self.model_class = model_class

    @classmethod
    def _get_analyzer_name(cls, analyzer_type):
        analyzer_settings = search_settings["analyzers"][analyzer_type.value]
        return analyzer_settings["es_analyzer"]

    @classmethod
    def _get_searchable_search_fields(cls, model_field_name, analyzers, boost=1.0):
        fields = []
        if len(analyzers) == 0:
            analyzers = [AnalysisType.TOKENIZED]

        for analyzer in analyzers:
            index_field_name = get_indexed_field_name(model_field_name, analyzer)
            fields += [
                SearchField(
                    index_field_name,
                    model_field_name=model_field_name,
                    es_extra={
                        "analyzer": cls._get_analyzer_name(analyzer),
                    },
                    boost=boost,
                ),
            ]
        return fields

    @classmethod
    def _get_autocomplete_search_fields(cls, model_field_name):
        return [AutocompleteField(model_field_name)]

    @classmethod
    def _get_filterable_search_fields(cls, model_field_name):
        return [
            FilterField(model_field_name),
        ]

    # @classmethod
    # def _get_related_fields(cls, model_field_name, mapping):
    #     fields = []
    #     for related_field_mapping in mapping:
    #         fields += cls._get_search_fields_from_mapping(related_field_mapping)
    #     return [
    #         RelatedFields(model_field_name, fields),
    #     ]

    # @classmethod
    # def _get_search_fields_from_mapping(cls, field_mapping):
    #     fields = []
    #     model_field_name = field_mapping["model_field_name"]

    #     if "related_fields" in field_mapping:
    #         fields += cls._get_related_fields(
    #             model_field_name, field_mapping["related_fields"]
    #         )

    #     if "search" in field_mapping:
    #         fields += cls._get_searchable_search_fields(
    #             model_field_name,
    #             field_mapping["search"],
    #             field_mapping["boost"],
    #         )

    #     if "autocomplete" in field_mapping:
    #         fields += cls._get_autocomplete_search_fields(model_field_name)

    #     if "filter" in field_mapping:
    #         fields += cls._get_filterable_search_fields(model_field_name)

    #     return fields

    @classmethod
    def get_mapping(cls, model_class):
        return [
            field.mapping
            for field in model_class.get_search_fields()
            if hasattr(field, "mapping")
        ]

    # @classmethod
    # def get_search_fields(cls):
    #     cls.generated_fields = []
    #     for field_mapping in cls.get_mapping():
    #         cls.generated_fields += cls._get_search_fields_from_mapping(field_mapping)
    #     return cls.generated_fields

    @classmethod
    def get_directly_defined_fields(cls):
        if not cls.generated_fields or len(cls.generated_fields) == 0:
            cls.get_search_fields()

        index_field_names = [f.model_field_name for f in cls.fields]
        return [
            field
            for field in cls.generated_fields
            if (
                hasattr(field, "model_field_name")
                and field.model_field_name in index_field_names
            )
        ]
