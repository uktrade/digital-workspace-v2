# type: ignore  (type checking is unhappy about the mixin referencing fields it doesnt define)
import inspect
import logging
from typing import Optional

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
    def get_indexed_fields(cls):
        cls.generated_fields = []
        if not hasattr(cls, "indexed_fields"):
            return []

        for (
            field
        ) in (
            cls.indexed_fields
        ):  # @TODO doesnt support SearchFields in indexed_fiedls (for now ?)
            cls.generated_fields += field.generate_fields()
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
    def __init__(
        self, field_name, *args, model_field_name=None, parent_field=None, **kwargs
    ):
        super().__init__(field_name, *args, **kwargs)
        self.model_field_name = model_field_name or field_name
        self.parent_field = parent_field

    def get_field(self, cls):
        return cls._meta.get_field(self.model_field_name)

    def get_definition_model(self, cls):
        if base_cls := super().get_definition_model(cls):
            return base_cls

        # Find where it was defined by walking the inheritance tree
        for base_cls in inspect.getmro(cls):
            if self.get_base_model_field_name() in base_cls.__dict__:
                return base_cls

    def get_value(self, obj):
        if value := super().get_value(obj):
            return value

        value = getattr(obj, self.model_field_name, None)
        # if hasattr(value, "__call__"):  # noqa: B004
        #     value = value()
        return value

    #################################
    # RelatedField support in queries
    #################################

    def is_relation_of(self, field):
        """
        Allows post-init definiton of a field Relation (used for field name generation)
        """
        self.parent_field = field

    def get_base_field(self):
        """
        Returns the field on the indexed model that owns the relationship, or the field if no relation exists
        """
        if self.parent_field:
            return self.parent_field.get_base_field()
        return self

    def get_base_model_field_name(self):
        """
        Returns the model field name of the field on the model that owns the relationship, if any, or the field name if not.

        Examples (Book is the indexed model)
        Book -> Author -> First Name: this would return author
        Book -> Author -> Publisher -> Name: this would return author
        """
        return self.get_base_field().model_field_name

    def get_full_model_field_name(self):
        """
        Returns the full name of the field based on the relations in place, starting at the base indexed model.

        Examples (Book is the indexed model)
        Book -> Author -> First Name: this would return author.first_name
        Book -> Author -> Publisher -> Name: this would return author.publisher.name
        """
        if self.parent_field:
            return f"{self.parent_field.get_full_model_field_name()}.{self.model_field_name}"
        return self.model_field_name


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

    def generate_fields(
        self, parent_field: Optional[BaseField] = None
    ) -> list[BaseField]:
        if parent_field:
            self.is_relation_of(parent_field)

        generated_fields = []
        for field in self.fields:  # @TODO verify properly
            if isinstance(field, IndexedField) or isinstance(field, RelatedFields):
                generated_fields += field.generate_fields(parent_field=self)
            else:
                field.is_relation_of(self)  # <- won't work on wagtail native fields
                generated_fields.append(field)

        self.fields = generated_fields
        return [self]


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
        parent_field: Optional[BaseField] = None,
    ) -> list[BaseField]:
        generated_fields = []

        if parent_field:
            self.is_relation_of(parent_field)

        if self.search:
            generated_fields += self.generate_search_fields(parent_field)
        if self.autocomplete:
            generated_fields += self.generate_autocomplete_fields(parent_field)
        if self.filter:
            generated_fields += self.generate_filter_fields(parent_field)

        return generated_fields

    def generate_search_fields(
        self, parent_field: Optional[BaseField] = None
    ) -> list[SearchField]:
        generated_fields = []
        for variant_args, variant_kwargs in self.get_search_field_variants():
            kwargs = self.search_kwargs.copy()
            kwargs.update(variant_kwargs)
            generated_fields.append(
                SearchField(
                    *variant_args,
                    model_field_name=self.model_field_name,
                    boost=self.boost,
                    parent_field=parent_field,
                    **kwargs,
                )
            )
        return generated_fields

    def generate_autocomplete_fields(
        self, parent_field: Optional[BaseField] = None
    ) -> list[AutocompleteField]:
        generated_fields = []
        for variant_args, variant_kwargs in self.get_autocomplete_field_variants():
            kwargs = self.autocomplete_kwargs.copy()
            kwargs.update(variant_kwargs)
            generated_fields.append(
                AutocompleteField(
                    *variant_args,
                    model_field_name=self.model_field_name,
                    parent_field=parent_field,
                    **kwargs,
                )
            )
        return generated_fields

    def generate_filter_fields(
        self, parent_field: Optional[BaseField] = None
    ) -> list[FilterField]:
        generated_fields = []
        for variant_args, variant_kwargs in self.get_filter_field_variants():
            kwargs = self.filter_kwargs.copy()
            kwargs.update(variant_kwargs)
            generated_fields.append(
                FilterField(
                    *variant_args,
                    model_field_name=self.model_field_name,
                    parent_field=parent_field,
                    **kwargs,
                )
            )
        return generated_fields

    def get_search_field_variants(self) -> list[tuple[tuple, dict]]:
        """
        Override this in order to customise the args and kwargs passed to SearchField on creation or to create more than one, each with different kwargs
        """
        if self.search:
            return [
                ((self.model_field_name,), {}),
            ]
        return []

    def get_autocomplete_field_variants(self) -> list[tuple[tuple, dict]]:
        """
        Override this in order to customise the args and kwargs passed to AutocompleteField on creation or to create more than one, each with different kwargs
        """
        if self.autocomplete:
            return [
                ((self.model_field_name,), {}),
            ]
        return []

    def get_filter_field_variants(self) -> list[tuple[tuple, dict]]:
        """
        Override this in order to customise the args and kwargs passed to FilterField on creation or to create more than one, each with different kwargs
        """
        if self.filter:
            return [
                ((self.model_field_name,), {}),
            ]
        return []


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

    def get_search_analyzers(self):
        analyzers = set()
        if self.tokenized:
            analyzers.add(AnalysisType.TOKENIZED)
        if self.explicit:
            analyzers.add(AnalysisType.EXPLICIT)
        if not analyzers and self.search:
            analyzers.add(AnalysisType.TOKENIZED)
        return analyzers

    def get_autocomplete_analyzers(self):
        analyzers = set()
        if self.autocomplete:  # @TODO
            analyzers.add(AnalysisType.NGRAM)
        return analyzers

    def get_filter_analyzers(self):
        analyzers = set()
        if self.filter:  # @TODO
            analyzers.add(AnalysisType.FILTER)
        return analyzers

    def get_search_field_variants(self):
        from extended_search.settings import extended_search_settings as search_settings
        from extended_search.managers import get_indexed_field_name

        return [
            (
                (get_indexed_field_name(self.model_field_name, analyzer),),
                {
                    "es_extra": {
                        "analyzer": search_settings["analyzers"][analyzer.value][
                            "es_analyzer"
                        ]
                    }
                },
            )
            for analyzer in self.get_search_analyzers()
        ]

    # def get_filter_field_variants(self):
    #     return super().get_filter_field_variants()

    # def get_autocomplete_field_variants(self):
    #     return super().get_autocomplete_field_variants()


# class MultiQueryRelatedField(RelatedField):
#     def __init__(self, *args: Any, **kwargs: Any) -> None:
#         super().__init__(*args, **kwargs)
#         self.indexed_fields = [
#             f
#             for f in self.fields
#             if isinstance(f, IndexedField) or isinstance(f, RelatedFields)
#         ]


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

    def get_search_analyzers(self):
        analyzers = super().get_search_analyzers()
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
