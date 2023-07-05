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
        self.search = kwargs["search"] = search
        self.autocomplete = kwargs["autocomplete"] = autocomplete
        self.filter = kwargs["filter"] = filter
        self.fuzzy = kwargs["fuzzy"] = fuzzy
        self.kwargs = kwargs

        if fuzzy:
            self.search = True

    def _get_search_mapping_object(self):
        if self.fuzzy:
            mapping = {
                "search": [
                    AnalysisType.TOKENIZED,
                ],
                "fuzzy": None,
            }
        else:
            mapping = {"search": []}
        return mapping

    def _get_autocomplete_mapping_object(self):
        return {"autocomplete": None}

    def _get_filter_mapping_object(self):
        return {"filter": None}

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
        proximity=False,  # @TODO How to implement this?
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.tokenized = kwargs["tokenized"] = tokenized
        self.explicit = kwargs["explicit"] = explicit
        self.keyword = kwargs["keyword"] = keyword
        self.proximity = kwargs["proximity"] = proximity

        if tokenized or explicit or keyword:
            self.search = True

    def _get_search_mapping_object(self):
        mapping = super()._get_search_mapping_object()
        if self.tokenized and AnalysisType.TOKENIZED not in mapping["search"]:
            mapping["search"] += [AnalysisType.TOKENIZED]
        if self.explicit:
            mapping["search"] += [AnalysisType.EXPLICIT]
        if self.keyword:
            mapping["search"] += [AnalysisType.KEYWORD]
        if self.proximity:
            mapping["search"] += [AnalysisType.PROXIMITY]
        return mapping


class RelatedIndexedFields(AbstractBaseField):
    def __init__(self, name, related_fields, *args, **kwargs):
        super().__init__(name, *args, **kwargs)
        self.related_fields = kwargs["related_fields"] = related_fields
        self.kwargs = kwargs

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
