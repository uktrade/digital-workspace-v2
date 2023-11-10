# type: ignore  (type checking is unhappy about the mixin referencing fields it doesnt define)
import inspect
import logging

from django.core import checks
from wagtail.search import index

logger = logging.getLogger(__name__)


class BaseField(index.BaseField):
    def __init__(self, field_name, model_field_name=None, **kwargs):
        super().__init__(field_name, **kwargs)
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
        if hasattr(value, "__call__"):
            value = value()
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
# UNPROCESSED STUFF BELOW @TODO
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


class CustomIndexed(Indexed):
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
