import logging

from extended_search.types import AnalysisType


logger = logging.getLogger(__name__)


class AbstractBaseField:
    def __init__(self, name, model_field_name=None, boost=1.0, **kwargs):
        self.name = kwargs["name"] = name
        self.model_field_name = kwargs["model_field_name"] = model_field_name or name
        self.boost = kwargs["boost"] = boost
        self.kwargs = kwargs

    def _get_base_mapping_object(self):
        return {
            "name": self.name,
            "model_field_name": self.model_field_name,
            "boost": self.boost,
        }

    def get_mapping(self):
        return self._get_base_mapping_object()

    @property
    def mapping(self):
        return self.get_mapping()


class BaseIndexedField(AbstractBaseField):
    def __init__(
        self,
        *args,
        search=False,
        autocomplete=False,
        filter=False,
        fuzzy=False,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.search = self.kwargs["search"] = search
        self.autocomplete = self.kwargs["autocomplete"] = autocomplete
        self.filter = self.kwargs["filter"] = filter
        self.fuzzy = self.kwargs["fuzzy"] = fuzzy

        if fuzzy:
            self.search = True

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
        mapping = super().get_mapping()
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


class RelatedIndexedFields(AbstractBaseField):
    def __init__(self, name, related_fields, *args, **kwargs):
        super().__init__(name, *args, **kwargs)
        self.related_fields = self.kwargs["related_fields"] = related_fields

    def _get_related_mapping_object(self):
        fields = []
        for field in self.related_fields:
            fields += [field.get_mapping()]
        return {
            "related_fields": fields,
        }

    def get_mapping(self):
        mapping = super().get_mapping()
        return mapping | self._get_related_mapping_object()
