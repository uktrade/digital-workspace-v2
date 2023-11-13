import logging

from wagtail.search.index import FilterField

from extended_search.index import (
    AutocompleteField,
    IndexedField,
    RelatedFields,
    SearchField,
)
from extended_search.managers.query_builder import CustomQueryBuilder
from extended_search.settings import extended_search_settings as search_settings

logger = logging.getLogger(__name__)


class ModelIndexManager(CustomQueryBuilder):
    fields = []

    def __new__(cls):
        return cls.get_search_fields()

    @classmethod
    def _get_analyzer_name(cls, analyzer_type):
        analyzer_settings = search_settings["analyzers"][analyzer_type.value]
        return analyzer_settings["es_analyzer"]

    @classmethod
    def _get_searchable_search_fields(cls, field: IndexedField):
        from extended_search.managers import get_indexed_field_name

        fields = []
        # if len(analyzers) == 0:
        #     analyzers = [AnalysisType.TOKENIZED]

        for analyzer in field.get_analyzers():
            index_field_name = get_indexed_field_name(
                field.model_field_name,
                analyzer,
            )
            fields += [
                SearchField(
                    index_field_name,
                    model_field_name=field.model_field_name,
                    es_extra={
                        "analyzer": cls._get_analyzer_name(analyzer),
                    },
                    boost=field.boost,
                ),
            ]
        return fields

    @classmethod
    def _get_autocomplete_search_fields(cls, field: IndexedField):
        return [AutocompleteField(field.model_field_name)]

    @classmethod
    def _get_filterable_search_fields(cls, field: IndexedField):
        return [
            FilterField(field.model_field_name),
        ]

    @classmethod
    def _get_related_fields(cls, field: RelatedFields):
        fields = []
        for related_field in field.fields:
            fields += cls._get_search_fields(related_field)
        return [
            RelatedFields(field.model_field_name, fields),
        ]

    @classmethod
    def _get_search_fields(cls, field):
        fields = []

        if isinstance(field, RelatedFields):
            fields += cls._get_related_fields(field)

        if isinstance(field, IndexedField):
            if field.search:
                fields += cls._get_searchable_search_fields(field)

            if field.autocomplete:
                fields += cls._get_autocomplete_search_fields(field)

            if field.filter:
                fields += cls._get_filterable_search_fields(field)
        else:
            fields.append(field)

        return fields

    @classmethod
    def get_search_fields(cls):
        cls.generated_fields = []
        for field in cls.fields:
            cls.generated_fields += cls._get_search_fields(field)
        return cls.generated_fields

    @classmethod
    def get_directly_defined_fields(cls):
        if not cls.generated_fields or len(cls.generated_fields) == 0:
            cls.get_search_fields()

        index_field_names = [f.model_field_name for f in cls.fields]
        return [
            field
            for field in cls.generated_fields
            if (
                hasattr(field, "model_field_name")  # @TODO do we still need this line?
                and field.model_field_name in index_field_names
            )
        ]

    @classmethod
    def is_directly_defined(cls, field):
        return field in cls.get_directly_defined_fields()
