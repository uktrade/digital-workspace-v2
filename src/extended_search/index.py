# type: ignore  (type checking is unhappy about the mixin referencing fields it doesnt define)
import inspect
import logging
from typing import Optional, Type

from django.apps import apps
from django.core import checks
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models.fields.related import ForeignObjectRel, OneToOneRel, RelatedField
from modelcluster.fields import ParentalManyToManyField
from wagtail.search import index

from extended_search.types import AnalysisType


logger = logging.getLogger(__name__)


#############################
# Wagtail basic overrides
#############################


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

    indexed_fields = []

    @classmethod
    def get_indexed_fields(cls, as_dict: bool = False):
        processed_index_fields = {}
        class_mro = list(inspect.getmro(cls))
        class_mro.reverse()
        for model_class in class_mro:
            model_field_names = []
            if class_is_indexed(model_class) and issubclass(model_class, Indexed):
                for f in model_class.indexed_fields:
                    f.configuration_model = model_class
                    if isinstance(f, BaseField):
                        if f.model_field_name not in model_field_names:
                            processed_index_fields[f.model_field_name] = []
                            model_field_names.append(f.model_field_name)
                        processed_index_fields[f.model_field_name].append(f)
                    else:
                        if f.field_name not in model_field_names:
                            processed_index_fields[f.field_name] = []
                            model_field_names.append(f.field_name)
                        processed_index_fields[f.field_name].append(f)

        if as_dict:
            return processed_index_fields
        return [f for v in processed_index_fields.values() for f in v]

    @classmethod
    def generate_from_indexed_fields(cls):
        processed_index_fields = cls.get_indexed_fields(as_dict=True)

        # @TODO doesn't support SearchFields in indexed_fields (for now ?)
        for k, v in processed_index_fields.items():
            processed_index_fields[k] = []
            for f in v:
                processed_index_fields[k] += f.generate_fields(cls)
        return processed_index_fields

    processed_search_fields = {}

    @classmethod
    def get_search_fields(cls, ignore_cache=False):
        if cls not in cls.processed_search_fields:
            cls.processed_search_fields[cls] = []
        if cls.processed_search_fields[cls] and not ignore_cache:
            return cls.processed_search_fields[cls]

        search_fields = super().get_search_fields()
        processed_fields = {}

        for f in search_fields:
            pfn_key = getattr(f, "model_field_name", f.field_name)
            if pfn_key not in processed_fields:
                processed_fields[pfn_key] = []
            processed_fields[pfn_key].append(f)

        processed_fields |= cls.generate_from_indexed_fields()

        processed_search_fields = [f for v in processed_fields.values() for f in v]
        cls.processed_search_fields[cls] = processed_search_fields
        return processed_search_fields

    @classmethod
    def has_unique_index_fields(cls):
        # @TODO [DWPF-1066] this doesn't account for a diverging MRO
        parent_model = cls.indexed_get_parent()
        parent_indexed_fields = getattr(parent_model, "indexed_fields", [])
        return cls.indexed_fields != parent_indexed_fields

    @classmethod
    def get_score_functions(cls):
        return [
            field
            for field in cls.get_indexed_fields()
            if isinstance(field, ScoreFunction)
        ]

    @classmethod
    def get_root_index_model(cls):
        class_mro = list(inspect.getmro(cls))
        class_mro.reverse()
        for model in class_mro:
            if model != Indexed and issubclass(model, Indexed):
                return model
        return cls


def get_indexed_models() -> list[Type[Indexed]]:
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
        self,
        field_name,
        *args,
        model_field_name=None,
        parent_field=None,
        configuration_model=None,
        **kwargs,
    ):
        super().__init__(field_name, *args, **kwargs)
        self.model_field_name = model_field_name or field_name
        self.parent_field = parent_field
        self.configuration_model = configuration_model

    def get_field(self, cls):
        return cls._meta.get_field(self.model_field_name)

    def get_definition_model(self, cls):
        if self.configuration_model:
            return self.configuration_model

        if base_cls := super().get_definition_model(cls):
            return base_cls

        # Find where it was defined by walking the inheritance tree
        base_model_field_name = self.get_base_model_field_name()
        for base_cls in inspect.getmro(cls):
            if hasattr(base_cls, base_model_field_name):
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


class SearchField(index.SearchField, BaseField, index.BaseField): ...


class AutocompleteField(index.AutocompleteField, BaseField, index.BaseField): ...


class FilterField(index.FilterField, BaseField, index.BaseField): ...


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
        self,
        cls,
        parent_field: Optional[BaseField] = None,
        configuration_model: Optional[Type[Indexed]] = None,
    ) -> list[BaseField]:
        if parent_field:
            self.is_relation_of(parent_field)
        if configuration_model:
            self.configuration_model = configuration_model

        generated_fields = []
        for field in self.fields:
            if isinstance(field, IndexedField) or isinstance(field, RelatedFields):
                generated_fields += field.generate_fields(
                    cls,
                    parent_field=self,
                    configuration_model=self.configuration_model,
                )
            else:
                # is_relation_of won't work on Wagtail native fields
                field.is_relation_of(self)
                generated_fields.append(field)

        return [
            RelatedFields(
                field_name=self.field_name,
                model_field_name=self.model_field_name,
                parent_field=self.parent_field,
                configuration_model=self.configuration_model,
                fields=generated_fields,
            )
        ]

    def get_related_field(self, field_name):
        """
        Return the "child most" related field for a given field name.

        Example:
            `author.books.title` would return the title SearchField
        """
        for f in self.fields:
            if f.field_name == field_name:
                if isinstance(f, RelatedFields):
                    new_field_name = field_name.split(".")[1:]
                    return f.get_related_field(new_field_name)
                return f

    def __repr__(self) -> str:
        return f"<RelatedFields {self.field_name} fields={sorted([str(f) for f in self.fields])}>"


class ScoreFunction:
    SUPPORTED_FUNCTIONS = ["script_score", "gauss", "exp", "linear"]
    configuration_model: Optional[models.Model] = None

    def __init__(self, function_name, **kwargs) -> None:
        if function_name not in self.SUPPORTED_FUNCTIONS:
            raise AttributeError(
                f"Function {function_name} is not supported, expecting one of {', '.join(self.SUPPORTED_FUNCTIONS)}"
            )
        self.function_name = kwargs["function_name"] = function_name

        if function_name == "script_score":
            if "script" not in kwargs and "source" not in kwargs:
                raise AttributeError(
                    "The 'script_score' function type requires passing either a 'script' or a 'source' parameter"
                )

            if "script" in kwargs:
                if (
                    not isinstance(kwargs["script"], dict)
                    or "source" not in kwargs["script"]
                ):
                    raise AttributeError(
                        "The 'script' parameter must be a dict containing a 'source' key"
                    )
                self.script = kwargs["script"]
            elif "source" in kwargs:
                self.script = {"source": kwargs["source"]}

            self.params = {"script": self.script}

        else:  # it's a decay function
            if "field_name" not in kwargs:
                raise AttributeError(
                    f"The '{function_name}' function requires a 'field_name' parameter"
                )
            if "scale" not in kwargs:
                raise AttributeError(
                    f"The '{function_name}' function requires a 'scale' parameter"
                )
            if "decay" not in kwargs:
                # optional for ES, but we want explicit values in the config
                raise AttributeError(
                    f"The '{function_name}' function requires a 'decay' parameter"
                )
            self.field_name = kwargs["field_name"]
            self.scale = kwargs["scale"]
            self.decay = kwargs["decay"]
            self.params = {
                # TODO look into this field_name, see comment below
                "_field_name_": {  # NB important this is the model field name
                    "scale": self.scale,
                    "decay": self.decay,
                }
            }
            if "offset" in kwargs:
                self.offset = kwargs["offset"]
                self.params["_field_name_"]["offset"] = self.offset
            if "origin" in kwargs:
                self.origin = kwargs["origin"]
                self.params["_field_name_"]["origin"] = self.origin

    def get_score_name(self):
        if not self.configuration_model:
            raise AttributeError(
                "The configuration_model attribute must be set on the "
                "ScoreFunction instance to use it."
            )
        score_name = f"{self.field_name}_scorefunction"
        if self.configuration_model != self.configuration_model.get_root_index_model():
            score_name = (
                self.configuration_model._meta.app_label
                + "_"
                + self.configuration_model.__name__.lower()
                + "__"
                + score_name
            )
        return score_name

    def generate_fields(
        self,
        parent_field: Optional[BaseField] = None,
    ) -> list[BaseField]:
        generated_fields = []

        if self.field_name:
            generated_fields.append(
                FilterField(
                    self.get_score_name(),
                    model_field_name=self.field_name,
                    parent_field=parent_field,
                )
            )

        return generated_fields


#############################
# One-to-many supporting code
#############################


class IndexedField(BaseField):
    def __init__(
        self,
        *args,
        boost: float = 1.0,
        proximity: bool = False,
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
        self.proximity = proximity
        self.search = search
        self.search_kwargs = search_kwargs or {}
        self.autocomplete = autocomplete
        self.autocomplete_kwargs = autocomplete_kwargs or {}
        self.filter = filter
        self.filter_kwargs = filter_kwargs or {}

    def generate_fields(
        self,
        cls,
        parent_field: Optional[BaseField] = None,
        configuration_model: Optional[Type[Indexed]] = None,
    ) -> list[BaseField]:
        if parent_field:
            self.is_relation_of(parent_field)
        if configuration_model:
            self.configuration_model = configuration_model

        generated_fields = []

        if self.search:
            generated_fields += self.generate_search_fields(cls)
        if self.autocomplete:
            generated_fields += self.generate_autocomplete_fields(cls)
        if self.filter:
            generated_fields += self.generate_filter_fields(cls)

        return generated_fields

    def generate_search_fields(self, cls) -> list[SearchField]:
        generated_fields = []
        for variant_args, variant_kwargs in self.get_search_field_variants(cls):
            kwargs = self.search_kwargs.copy()
            kwargs.update(variant_kwargs)

            if "model_field_name" not in kwargs:
                kwargs["model_field_name"] = self.model_field_name

            if "boost" not in kwargs:
                kwargs["boost"] = self.boost

            if "parent_field" not in kwargs:
                kwargs["parent_field"] = self.parent_field

            if "configuration_model" not in kwargs:
                kwargs["configuration_model"] = self.configuration_model

            generated_fields.append(SearchField(*variant_args, **kwargs))
        return generated_fields

    def generate_autocomplete_fields(self, cls) -> list[AutocompleteField]:
        generated_fields = []
        for variant_args, variant_kwargs in self.get_autocomplete_field_variants(cls):
            kwargs = self.autocomplete_kwargs.copy()
            kwargs.update(variant_kwargs)

            if "model_field_name" not in kwargs:
                kwargs["model_field_name"] = self.model_field_name

            if "parent_field" not in kwargs:
                kwargs["parent_field"] = self.parent_field

            if "configuration_model" not in kwargs:
                kwargs["configuration_model"] = self.configuration_model

            generated_fields.append(AutocompleteField(*variant_args, **kwargs))
        return generated_fields

    def generate_filter_fields(self, cls) -> list[FilterField]:
        generated_fields = []
        for variant_args, variant_kwargs in self.get_filter_field_variants(cls):
            kwargs = self.filter_kwargs.copy()
            kwargs.update(variant_kwargs)

            if "model_field_name" not in kwargs:
                kwargs["model_field_name"] = self.model_field_name

            if "parent_field" not in kwargs:
                kwargs["parent_field"] = self.parent_field

            if "configuration_model" not in kwargs:
                kwargs["configuration_model"] = self.configuration_model

            generated_fields.append(FilterField(*variant_args, **kwargs))
        return generated_fields

    def get_search_field_variants(self, cls) -> list[tuple[tuple, dict]]:
        """
        Override this in order to customise the args and kwargs passed to SearchField on creation or to create more than one, each with different kwargs
        """
        if self.search:
            return [
                ((self.model_field_name,), {}),
            ]
        return []

    def get_autocomplete_field_variants(self, cls) -> list[tuple[tuple, dict]]:
        """
        Override this in order to customise the args and kwargs passed to AutocompleteField on creation or to create more than one, each with different kwargs
        """
        if self.autocomplete:
            return [
                ((self.model_field_name,), {}),
            ]
        return []

    def get_filter_field_variants(self, cls) -> list[tuple[tuple, dict]]:
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
        if self.autocomplete:
            analyzers.add(AnalysisType.NGRAM)
        return analyzers

    def get_filter_analyzers(self):
        analyzers = set()
        if self.filter:
            analyzers.add(AnalysisType.FILTER)
        return analyzers

    def get_search_field_variants(self, cls):
        from extended_search import settings as search_settings

        field_settings_key = search_settings.get_settings_field_key(cls, self)
        field_boosts = search_settings.extended_search_settings["boost_parts"]["fields"]
        field_boost = field_boosts.get(field_settings_key)

        search_field_variants = []

        for analyzer in self.get_search_analyzers():
            variant_args = (get_indexed_field_name(self.model_field_name, analyzer),)
            variant_kwargs = {
                "es_extra": {
                    "analyzer": search_settings.extended_search_settings["analyzers"][
                        analyzer.value
                    ]["es_analyzer"]
                },
            }

            if field_boost is not None:
                variant_kwargs["boost"] = float(field_boost)

            search_field_variants.append((variant_args, variant_kwargs))

        return search_field_variants


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


def get_indexed_field_name(
    model_field_name: str,
    analyzer: AnalysisType,
):
    from extended_search.settings import extended_search_settings

    field_name_suffix = (
        extended_search_settings["analyzers"][analyzer.value]["index_fieldname_suffix"]
        or ""
    )
    return f"{model_field_name}{field_name_suffix}"
