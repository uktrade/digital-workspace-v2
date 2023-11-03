# type: ignore  (type checking is unhappy about the mixin referencing fields it doesnt define)
import inspect
import logging

from django.core import checks
from wagtail.search import index


logger = logging.getLogger(__name__)


class Indexed(index.Indexed):
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

    search_fields = []


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
            hasattr(cls, "has_indexmanager_direct_inner_class")
            and cls.has_indexmanager_direct_inner_class()
            and cls.IndexManager.is_directly_defined(self)
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


class SearchField(RenamedFieldMixin, index.SearchField):
    ...


class AutocompleteField(RenamedFieldMixin, index.AutocompleteField):
    ...


class RelatedFields(RenamedFieldMixin, index.RelatedFields):
    ...
