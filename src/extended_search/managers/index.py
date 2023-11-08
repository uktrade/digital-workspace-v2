import logging

from extended_search.managers.query_builder import NestedQueryBuilder
from extended_search.settings import extended_search_settings as search_settings

logger = logging.getLogger(__name__)


class ExtendedSearchQueryBuilder(NestedQueryBuilder):
    def __init__(self, model_class, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_class = model_class

    def get_mapping(self):
        return [
            field.get_mapping()
            for _, field in self.model_class.get_indexed_fields().items()
        ]
