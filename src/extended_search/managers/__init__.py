import inspect
import logging
from typing import Optional

from wagtail.search.index import get_indexed_models
from wagtail.search.query import SearchQuery

from extended_search.backends.query import Filtered
from extended_search.managers.query_builder import CustomQueryBuilder
from extended_search.settings import extended_search_settings as search_settings
from extended_search.types import AnalysisType

logger = logging.getLogger(__name__)


def get_indexed_field_name(
    model_field_name: str,
    analyzer: AnalysisType,
    parent_model_field: Optional[str] = None,
):
    if parent_model_field:
        model_field_name = f"{parent_model_field}.{model_field_name}"

    field_name_suffix = (
        search_settings[f"analyzers__{analyzer.value}__index_fieldname_suffix"] or ""
    )
    return f"{model_field_name}{field_name_suffix}"

