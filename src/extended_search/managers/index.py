import logging

from wagtail.search.index import FilterField

from extended_search.index import AutocompleteField, RelatedFields, SearchField
from extended_search.managers import get_indexed_field_name
from extended_search.managers.query_builder import NestedQueryBuilder
from extended_search.settings import extended_search_settings as search_settings
from extended_search.types import AnalysisType

logger = logging.getLogger(__name__)


class ExtendedSearchQueryBuilder(NestedQueryBuilder):
    def __init__(self, model_class, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_class = model_class

    @classmethod
    def get_mapping(cls, model_class):
        return [
            field.get_mapping()
            for field in model_class.get_search_fields()
            if hasattr(field, "get_mapping")
        ]
