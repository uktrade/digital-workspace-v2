# type: ignore  (type checking is unhappy about the mixin referencing fields it doesnt define)
import inspect
import logging

from django.core import checks
from wagtail.search import index


logger = logging.getLogger(__name__)


class Indexed(index.Indexed):
    @classmethod
    def _check_search_fields(cls, **kwargs):
        errors = []
        for field in cls.get_search_fields():
            message = "{model}.search_fields contains non-existent field '{name}'"
            if not cls._has_field(field.field_name) and not cls._has_field(
                field._get_model_field_name()
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

    def _get_model_field_name(self):
        try:
            return self.kwargs["model_field_name"]
        except AttributeError:
            return None

    def get_field(self, cls):
        """
        Returns the underlying model's field_name in preference to the name assigned, which may include the analysis type suffix
        """
        if field := cls._meta.get_field(self._get_model_field_name()):
            return field

        return super().get_field(cls)

    def get_attname(self, cls):
        """
        Returns the assigned field name (including the analysis type suffix) in preference to the underlying model's field_name, but only if they differ in kwargs - i.e. the field is not a property, but does have a different name to the model attribute
        """
        if self._get_model_field_name() != self.field_name:
            return self.field_name

        return super().get_attname(cls)

    def get_definition_model(self, cls):
        """
        Returns the correct base class if it wasn't found because of a field naming discrepancy
        """
        if not (base_cls := super().get_definition_model(cls)):
            for base_cls in inspect.getmro(cls):
                if self._get_model_field_name() in base_cls.__dict__:
                    return base_cls

        return base_cls

    def get_value(self, obj):
        """
        Returns the value from the model's field if it wasnt found because of a naming discrepancy
        """
        if not (value := super().get_value(obj)):
            value = getattr(obj, self._get_model_field_name(), None)
        return value


class SearchField(RenamedFieldMixin, index.SearchField):
    ...


class AutocompleteField(RenamedFieldMixin, index.AutocompleteField):
    ...


class RelatedFields(RenamedFieldMixin, index.RelatedFields):
    ...
