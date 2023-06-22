import logging
from wagtail.search import index

from typing import Any, Collection, Dict

logger = logging.getLogger(__name__)


class RenamedFieldMixin:
    def get_field(self, cls):
        if not isinstance(self, index.BaseField):
            raise Exception("RenamedFieldMixin expects to operate on a class inherited from wagtail.search.index.BaseField")

        if "model_field_name" in self.kwargs:
            return cls._meta.get_field(self.kwargs["model_field_name"])
        return super().get_field(cls)


class SearchField(RenamedFieldMixin, index.SearchField):
    ...


class AutocompleteField(RenamedFieldMixin, index.AutocompleteField):
    ...
