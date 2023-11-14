# type: ignore  (type checking is unhappy about the mixin referencing fields it doesnt define)
import inspect
import logging
from typing import Optional, Union

from django.apps import apps
from django.core import checks
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models.fields.related import ForeignObjectRel, OneToOneRel, RelatedField
from extended_search.types import AnalysisType
from modelcluster.fields import ParentalManyToManyField
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

    ##################################
    # COPIED FROM INDEXMANAGER
    ##################################
    indexed_fields = []

    @classmethod
    def _get_analyzer_name(cls, analyzer_type):
        from extended_search.settings import extended_search_settings as search_settings

        analyzer_settings = search_settings["analyzers"][analyzer_type.value]
        return analyzer_settings["es_analyzer"]

    @classmethod
    def _get_searchable_search_fields(cls, field: "IndexedField"):
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
    def _get_autocomplete_search_fields(cls, field: "IndexedField"):
        return [AutocompleteField(field.model_field_name)]

    @classmethod
    def _get_filterable_search_fields(cls, field):
        return [
            FilterField(field.model_field_name),
        ]

    @classmethod
    def _get_related_fields(cls, field: "IndexedField"):
        fields = []
        for related_field in field.fields:
            fields += cls._get_indexed_fields(related_field)
        return [
            RelatedFields(field.model_field_name, fields),
        ]

    @classmethod
    def _get_indexed_fields(cls, field: Union["RelatedFields", "IndexedField"]):
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
    def get_indexed_fields(cls):
        cls.generated_fields = []
        if not hasattr(cls, "indexed_fields"):
            return []

        for field in cls.indexed_fields:
            cls.generated_fields += cls._get_indexed_fields(field)
        return cls.generated_fields

    @classmethod
    def get_directly_defined_fields(cls):
        if not cls.generated_fields or len(cls.generated_fields) == 0:
            cls.get_indexed_fields()

        index_field_names = [f.model_field_name for f in cls.indexed_fields]
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

    ##################################
    # END OF COPYPASTA
    # EXTRAS TO MAKE IT WORK BELOW
    ##################################

    @classmethod
    def get_search_fields(cls):
        search_fields = super().get_search_fields()
        processed_index_fields = []
        for model_class in inspect.getmro(cls):
            if class_is_indexed(model_class) and issubclass(model_class, Indexed):
                processed_index_fields += model_class.get_indexed_fields()

        return search_fields + processed_index_fields

    @classmethod
    def get_all_indexed_fields_including_from_parents_and_refactor_this(cls):
        fields = set()
        for model_class in inspect.getmro(cls):
            if class_is_indexed(model_class) and issubclass(model_class, Indexed):
                fields.update(model_class.indexed_fields)
        return list(fields)


def get_indexed_models():
    """
    Overrides wagtail.search.index.get_indexed_models
    """
    return [
        model
        for model in apps.get_models()
        if issubclass(model, index.Indexed) and not model._meta.abstract
        # and model.search_fields
    ]


def class_is_indexed(cls):
    """
    Overrides wagtail.search.index.class_is_indexed
    """
    return (
        issubclass(cls, index.Indexed)
        and issubclass(cls, models.Model)
        and not cls._meta.abstract
        # and cls.search_fields
    )
    ##################################
    # END OF EXTRAS
    ##################################


class ModelFieldNameMixin:
    def __init__(self, field_name, *args, model_field_name=None, **kwargs):
        super().__init__(field_name, *args, **kwargs)
        self.model_field_name = model_field_name or field_name

    def get_field(self, cls):
        return cls._meta.get_field(self.model_field_name)

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


class BaseField(ModelFieldNameMixin, index.BaseField):
    def get_attname(self, cls):
        if self.model_field_name != self.field_name:
            return self.field_name
        return super().get_attname(cls)


class SearchField(index.SearchField, BaseField, index.BaseField):
    ...


class AutocompleteField(index.AutocompleteField, BaseField, index.BaseField):
    ...


class FilterField(index.FilterField, BaseField, index.BaseField):
    ...


class RelatedFields(ModelFieldNameMixin, index.RelatedFields):
    def select_on_queryset(self, queryset):
        """
        This method runs either prefetch_related or select_related on the queryset
        to improve indexing speed of the relation.

        It decides which method to call based on the number of related objects:
         - single (eg ForeignKey, OneToOne), it runs select_related
         - multiple (eg ManyToMany, reverse ForeignKey) it runs prefetch_related
        """
        try:
            field = self.get_field(queryset.model)
        except FieldDoesNotExist:
            return queryset

        if isinstance(field, RelatedField) and not isinstance(
            field, ParentalManyToManyField
        ):
            if field.many_to_one or field.one_to_one:
                queryset = queryset.select_related(self.model_field_name)
            elif field.one_to_many or field.many_to_many:
                queryset = queryset.prefetch_related(self.model_field_name)

        elif isinstance(field, ForeignObjectRel):
            # Reverse relation
            if isinstance(field, OneToOneRel):
                # select_related for reverse OneToOneField
                queryset = queryset.select_related(self.model_field_name)
            else:
                # prefetch_related for anything else (reverse ForeignKey/ManyToManyField)
                queryset = queryset.prefetch_related(self.model_field_name)

        return queryset


#############################
# Wagtail overrides above
# Our custom code below
#############################


#############################
# One-to-many supporting code
#############################


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

    def get_analyzers(self):
        analyzers = set()
        if self.search:
            analyzers.add(AnalysisType.TOKENIZED)
        # @TODO add analyzers for filter, autocomplete
        return analyzers


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

    def get_analyzers(self):
        analyzers = super().get_analyzers()
        if self.explicit:
            analyzers.add(AnalysisType.EXPLICIT)
        if self.tokenized:
            analyzers.add(AnalysisType.TOKENIZED)
        return analyzers


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

    def get_analyzers(self):
        analyzers = super().get_analyzers()
        if self.keyword:
            analyzers.add(AnalysisType.KEYWORD)
        return analyzers


#############################
# UNPROCESSED STUFF BELOW @TODO
#############################


class CustomIndexed(Indexed):
    @classmethod
    def has_indexmanager_direct_inner_class(cls):
        for attr in cls.__dict__.values():
            if (
                inspect.isclass(attr)
                # and issubclass(attr, ModelIndexManager) #  Can't run this check due to circular imports
                and (
                    attr.__name__ == "IndexManager" or attr.__name__ == "indexed_fields"
                )
            ):
                return True
        return False

    search_fields = []
