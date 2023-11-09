import logging
from typing import Optional

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


def get_search_query(index_manager, query_str, model_class, *args, **kwargs):
    """
    Uses the field mapping to derive the full nested SearchQuery
    """
    query = None
    for field_mapping in index_manager.get_mapping():
        query_elements = index_manager._get_search_query_from_mapping(
            query_str, model_class, field_mapping
        )
        if query_elements is not None:
            query = index_manager._combine_queries(
                query,
                query_elements,
            )

    logger.debug(query)
    return query
