import inspect
import logging
from django.core.exceptions import FieldDoesNotExist
from wagtail.search import index


from typing import Any, Collection, Dict

logger = logging.getLogger(__name__)


class RenamedFieldMixin:
    def get_field(self, cls):
        if "kwargs" in self.__dict__ and "model_field_name" in self.kwargs:
            return cls._meta.get_field(self.kwargs["model_field_name"])
        return super().get_field(cls)

    def get_definition_model(self, cls):
        base_cls = super().get_definition_model(cls)
        if (
            base_cls is None and
            "kwargs" in self.__dict__ and
            "model_field_name" in self.kwargs
        ):
            for base_cls in inspect.getmro(cls):
                if self.kwargs["model_field_name"] in base_cls.__dict__:
                    return base_cls
        return base_cls

    def get_value(self, obj):
        value = super().get_value(obj)
        if (
            value is None and
            "kwargs" in self.__dict__ and
            "model_field_name" in self.kwargs
        ):
            value = getattr(obj, self.kwargs["model_field_name"], None)
        return value


class SearchField(RenamedFieldMixin, index.SearchField):
    ...


class AutocompleteField(RenamedFieldMixin, index.AutocompleteField):
    ...


class RelatedFields(RenamedFieldMixin, index.RelatedFields):
    ...
