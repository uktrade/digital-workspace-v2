# type: ignore  (type checking is unhappy about the mixin referencing fields it doesnt define)
import inspect
import logging
from typing import Optional

from django.core import checks
from wagtail.search import index

logger = logging.getLogger(__name__)


class Indexed(index.Indexed):
    search_fields = []

    @classmethod
    def _check_search_fields(cls, **kwargs):
        errors = []
        for field in cls.get_search_fields():
            message = "{model}.search_fields contains non-existent field '{name}'"
            if not cls._has_field(field.field_name) and not cls._has_field(
                field.model_field_name
            ):
                errors.append(
                    checks.Warning(
                        message.format(model=cls.__name__, name=field.field_name),
                        obj=cls,
                        id="wagtailsearch.W004",
                    )
                )
        return errors


class BaseField(index.BaseField):
    def __init__(self, field_name, *args, model_field_name=None, **kwargs):
        super().__init__(field_name, *args, **kwargs)
        self.model_field_name = model_field_name or field_name

    def get_field(self, cls):
        return cls._meta.get_field(self.model_field_name)

    def get_attname(self, cls):
        if self.model_field_name != self.field_name:
            return self.field_name
        return super().get_attname(cls)

    def get_definition_model(self, cls):
        if base_cls := super().get_definition_model(cls):
            return base_cls

        # # TODO: review this later (RelatedFields)
        # name_parts = model_field_name.split(".")
        # if len(name_parts) > 1:
        #     model_field_name = name_parts[0]

        # Find where it was defined by walking the inheritance tree
        for base_cls in inspect.getmro(cls):
            if self.model_field_name in base_cls.__dict__:
                return base_cls

    def get_value(self, obj):
        if value := super().get_value(obj):
            return value

        value = getattr(obj, self.model_field_name, None)
        # if hasattr(value, "__call__"):  # noqa: B004
        #     value = value()
        return value


class SearchField(index.SearchField, BaseField, index.BaseField):
    ...


class AutocompleteField(index.AutocompleteField, BaseField, index.BaseField):
    ...


class FilterField(index.FilterField, BaseField, index.BaseField):
    ...


class RelatedFields(index.RelatedFields, BaseField, index.BaseField):
    ...


#############################
# Wagtail overrides above
# Our custom code below
#############################


#############################
# One-to-many supporting code
#############################


class OneToManyIndexed(Indexed):
    @classmethod
    def _get_search_field(cls, field_dict, field, parent_field):
        if isinstance(field, IndexedField):
            generated_fields = field.generate_fields()
            # generated_fields = field.generate_fields(parent_field)
            for generated_field in generated_fields:
                field_dict[
                    (type(generated_field), generated_field.field_name)
                ] = generated_field
        # elif isinstance(field, RelatedFields):
        #     related_fields = {}
        #     for related_field in field.fields:
        #         related_fields |= cls._get_search_field(related_field, field)
        #     field_dict[(RelatedFields, field.field_name)] = RelatedFields(
        #         field.model_field_name, list(related_fields.values())
        #     )
        else:
            if hasattr(field, "model_field_name"):
                field_dict[
                    (type(field), field.field_name, field.model_field_name)
                ] = field
            else:
                field_dict[(type(field), field.field_name)] = field
        return field_dict

    @classmethod
    def get_search_fields(cls, parent_field=None):
        search_fields = {}

        for field in cls.search_fields:
            search_fields |= cls._get_search_field(search_fields, field, parent_field)

        return list(search_fields.values())


class IndexedField(BaseField):
    def __init__(
        self,
        *args,
        boost: float = 1.0,
        search: bool = False,
        search_kwargs: Optional[dict] = None,
        autocomplete: bool = False,
        autocomplete_kwargs: Optional[dict] = None,
        filter: bool = False,
        filter_kwargs: Optional[dict] = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.boost = boost
        self.search = search
        self.search_kwargs = search_kwargs or {}
        self.autocomplete = autocomplete
        self.autocomplete_kwargs = autocomplete_kwargs or {}
        self.filter = filter
        self.filter_kwargs = filter_kwargs or {}

    def generate_fields(
        self,
        # parent_field: Optional[BaseField] = None,
    ) -> list[BaseField]:
        generated_fields = []
        field_name = self.model_field_name
        # if parent_field:
        #     field_name = f"{parent_field.model_field_name}.{field_name}"

        if self.search:
            generated_fields.append(self.generate_search_field(field_name))
        if self.autocomplete:
            generated_fields.append(self.generate_autocomplete_field(field_name))
        if self.filter:
            generated_fields.append(self.generate_filter_field(field_name))

        return generated_fields

    def generate_search_field(self, field_name: str) -> SearchField:
        return SearchField(
            field_name,
            model_field_name=self.model_field_name,
            **self.search_kwargs,
        )

    def generate_autocomplete_field(self, field_name: str) -> AutocompleteField:
        return AutocompleteField(
            field_name,
            model_field_name=self.model_field_name,
            **self.autocomplete_kwargs,
        )

    def generate_filter_field(self, field_name: str) -> FilterField:
        return FilterField(
            field_name,
            model_field_name=self.model_field_name,
            **self.filter_kwargs,
        )


class RelatedIndexedFields(BaseField):
    def __init__(
        self,
        field_name: str,
        related_fields: list[BaseField],
        *args,
        **kwargs,
    ):
        super().__init__(field_name, *args, **kwargs)
        self.related_fields = related_fields


#############################
# Multi-query search code
#############################


class MultiQueryIndexedField(IndexedField):
    def __init__(
        self,
        *args,
        tokenized: bool = False,
        explicit: bool = False,
        fuzzy: bool = False,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.tokenized = tokenized
        self.explicit = explicit
        self.fuzzy = fuzzy

        if tokenized or explicit or fuzzy:
            self.search = True


#############################
# Digital Workspace code
#############################


class DWIndexedField(MultiQueryIndexedField):
    def __init__(
        self,
        *args,
        keyword: bool = False,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.keyword = keyword

        if keyword:
            self.search = True


#############################
# UNPROCESSED STUFF BELOW @TODO
#############################


class CustomIndexed(OneToManyIndexed):
    @classmethod
    def has_indexmanager_direct_inner_class(cls):
        for attr in cls.__dict__.values():
            if (
                inspect.isclass(attr)
                # and issubclass(attr, ModelIndexManager) #  Can't run this check due to circular imports
                and attr.__name__ == "IndexManager"
            ):
                return True
        return False

    search_fields = []

    @classmethod
    def _get_analyzer_name(cls, analyzer_type):
        from extended_search.settings import extended_search_settings

        analyzer_settings = extended_search_settings["analyzers"][analyzer_type.value]
        return analyzer_settings["es_analyzer"]

    @classmethod
    def _get_searchable_search_fields(cls, model_field_name, analyzers, boost=1.0):
        from extended_search.managers import get_indexed_field_name

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
        fields = []
        model_field_name = field_mapping["model_field_name"]

        if "related_fields" in field_mapping:
            fields += cls._get_related_fields(
                model_field_name, field_mapping["related_fields"]
            )

        if "search" in field_mapping:
            fields += cls._get_searchable_search_fields(
                model_field_name,
                field_mapping["search"],
                field_mapping["boost"],
            )

        if "autocomplete" in field_mapping:
            fields += cls._get_autocomplete_search_fields(model_field_name)

        if "filter" in field_mapping:
            fields += cls._get_filterable_search_fields(model_field_name)

        return fields

    @classmethod
    def get_mapping(cls):
        from extended_search.fields import BaseIndexedField

        mapping = []
        for field in cls.search_fields:
            if isinstance(field, BaseIndexedField):
                mapping += [
                    field.mapping,
                ]
        logger.debug(mapping)
        return mapping

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
                hasattr(field, "model_field_name")  # @TODO do we still need this line?
                and field.model_field_name in index_field_names
            )
        ]

    @classmethod
    def is_directly_defined(cls, field):
        return field in cls.get_directly_defined_fields()
