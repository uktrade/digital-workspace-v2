import logging

from extended_search import index
from extended_search.types import AnalysisType

logger = logging.getLogger(__name__)


class BaseIndexedField(index.IndexedField):
    def __init__(
        self,
        *args,
        fuzzy=False,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.fuzzy = self.kwargs["fuzzy"] = fuzzy

        if fuzzy:
            self.search = True

    def _get_base_mapping_object(self):
        return {
            "name": self.field_name,
            "model_field_name": self.model_field_name,
            "boost": self.boost,
            "parent_model_field": None,  # when is not None, field is Related
        }

    @property
    def mapping(self):
        return self.get_mapping()

    def _get_search_mapping_object(self):
        if not self.search:
            return {}

        mapping = {"search": []}

        if self.fuzzy:
            mapping["search"] = [
                AnalysisType.TOKENIZED,
            ]
            mapping["fuzzy"] = []

        return mapping

    def _get_autocomplete_mapping_object(self):
        if not self.autocomplete:
            return {}

        return {"autocomplete": []}

    def _get_filter_mapping_object(self):
        if not self.filter:
            return {}

        return {"filter": []}

    def get_mapping(self):
        mapping = self._get_base_mapping_object()
        if self.search:
            mapping = mapping | self._get_search_mapping_object()
        if self.autocomplete:
            mapping = mapping | self._get_autocomplete_mapping_object()
        if self.filter:
            mapping = mapping | self._get_filter_mapping_object()
        return mapping


class IndexedField(BaseIndexedField):
    def __init__(
        self,
        *args,
        tokenized=False,
        explicit=False,
        keyword=False,
        proximity=False,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.tokenized = self.kwargs["tokenized"] = tokenized
        self.explicit = self.kwargs["explicit"] = explicit
        self.keyword = self.kwargs["keyword"] = keyword
        self.proximity = self.kwargs["proximity"] = proximity

        if tokenized or explicit or keyword:
            self.search = True

        if proximity:
            self.filter = True

    def _get_search_mapping_object(self):
        mapping = super()._get_search_mapping_object()
        if self.tokenized and AnalysisType.TOKENIZED not in mapping["search"]:
            mapping["search"] += [AnalysisType.TOKENIZED]
        if self.explicit:
            mapping["search"] += [AnalysisType.EXPLICIT]
        if self.keyword:
            mapping["search"] += [AnalysisType.KEYWORD]
        return mapping

    def _get_filter_mapping_object(self):
        mapping = super()._get_filter_mapping_object()
        if self.proximity and AnalysisType.PROXIMITY not in mapping["filter"]:
            mapping["filter"] += [
                AnalysisType.PROXIMITY
            ]  # @TODO is this the right way to index proximity
        return mapping


class RelatedIndexedFields(index.RelatedIndexedFields):
    def _get_related_mapping_object(self):
        fields = []
        for field in self.related_fields:
            field_mapping = field.get_mapping()
            field_mapping["parent_model_field"] = self.model_field_name
            fields += [field_mapping]
        return {
            "related_fields": fields,
        }

    def _get_base_mapping_object(self):
        return {
            "name": self.field_name,
            "model_field_name": self.model_field_name,
            "parent_model_field": None,  # when is not None, field is Related
        }

    def get_mapping(self):
        mapping = self._get_base_mapping_object()
        return mapping | self._get_related_mapping_object()

    @property
    def mapping(self):
        return self.get_mapping()
