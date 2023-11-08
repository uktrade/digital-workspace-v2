# type: ignore  (type checking is unhappy about the mixin referencing fields it
# doesn't define)
import inspect
import logging
from typing import Dict, List

from django.core import checks
from wagtail.search import index

from extended_search.fields import IndexedField

logger = logging.getLogger(__name__)


class Indexed(index.Indexed):
    search_fields: List[IndexedField | index.BaseField | index.RelatedFields] = []
    indexed_fields: Dict[str, IndexedField | index.BaseField | index.RelatedFields] = {}

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

    @classmethod
    def _get_search_field(cls, field_dict, field, parent_field):
        if isinstance(field, IndexedField):
            generated_fields = field.generate_fields(parent_field)
            for generated_field in generated_fields:
                field_dict[
                    (type(generated_field), generated_field.field_name)
                ] = generated_field
        elif isinstance(field, RelatedFields):
            related_fields = {}
            for related_field in field.fields:
                related_fields |= cls._get_search_field(related_field, field)
            field_dict[(RelatedFields, field.field_name)] = RelatedFields(
                field.model_field_name, list(related_fields.values())
            )
        else:
            field_dict[(type(field), field.field_name, field.model_field_name)] = field
        return field_dict

    @classmethod
    def get_search_fields(cls, parent_field=None):
        search_fields = {}

        for field in cls.search_fields:
            search_fields |= cls._get_search_field(search_fields, field, parent_field)

        for _, field in cls.get_indexed_fields().items():
            search_fields |= cls._get_search_field(search_fields, field, parent_field)

        return list(search_fields.values())

    @classmethod
    def get_parent_model_indexed_fields(cls):
        for base_cls in inspect.getmro(cls)[1:]:
            if hasattr(base_cls, "get_indexed_fields"):
                return base_cls.get_indexed_fields()
        return {}

    @classmethod
    def get_indexed_fields(cls):
        parent_indexed_fields = cls.get_parent_model_indexed_fields()
        return parent_indexed_fields | cls.indexed_fields

    @classmethod
    def has_direct_indexed_fields(cls) -> bool:
        parent_indexed_fields = cls.get_parent_model_indexed_fields()
        current_indexed_fields = cls.get_indexed_fields()
        return parent_indexed_fields != current_indexed_fields


class RenamedFieldMixin:
    """
    Add this Mixin to wagtailsearch.index.BaseField and descendent classes to
    support renaming the field. It does this by adding a "model_field_name"
    kwarg that defaults to the field name.

    This is useful if you want your model and index fields to have a many to
    one relationship - e.g. if you are analyzing the same field multiple times.
    """

    @property
    def model_field_name(self):
        try:
            return self.kwargs["model_field_name"]
        except (AttributeError, KeyError):
            ...

        return None

    def get_field(self, cls):
        """
        Returns the underlying model's field_name in preference to the name assigned, which may include the analysis type suffix
        """
        if self.model_field_name:
            return cls._meta.get_field(self.model_field_name)
        return super().get_field(cls)

    def get_attname(self, cls):
        """
        Returns the assigned field name (including the analysis type suffix) in preference to the underlying model's field_name, but only if they differ in kwargs - i.e. the field is not a property, but does have a different name to the model attribute
        """
        if self.model_field_name and self.model_field_name != self.field_name:
            return self.field_name

        return super().get_attname(cls)

    def get_definition_model(self, cls):
        """
        Returns the correct base class if it wasn't found because of a field naming discrepancy
        """
        if (
            hasattr(cls, "has_direct_indexed_fields")
            and cls.has_direct_indexed_fields()
            # TODO: Update this check
            # and cls.IndexManager.is_directly_defined(self)
        ):
            return cls

        if base_cls := super().get_definition_model(cls):
            return base_cls

        if self.model_field_name:
            field_name = self.model_field_name

            # fields can have a dot-notation name if RelatedFields
            name_parts = field_name.split(".")
            if len(name_parts) > 1:
                field_name = name_parts[0]

            for base_cls in inspect.getmro(cls):
                if field_name in base_cls.__dict__:
                    return base_cls

    def get_value(self, obj):
        """
        Returns the value from the model's field if it wasnt found because of a naming discrepancy
        """
        if value := super().get_value(obj):
            return value

        if self.model_field_name:
            return getattr(obj, self.model_field_name, None)


class FilterField(RenamedFieldMixin, index.FilterField):
    ...


class SearchField(RenamedFieldMixin, index.SearchField):
    ...


class AutocompleteField(RenamedFieldMixin, index.AutocompleteField):
    ...


class RelatedFields(RenamedFieldMixin, index.RelatedFields):
    ...
