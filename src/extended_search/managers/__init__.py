import logging


from extended_search.settings import extended_search_settings as search_settings
from extended_search.types import AnalysisType

logger = logging.getLogger(__name__)


def get_indexed_field_name(
    model_field_name: str,
    analyzer: AnalysisType,
):
    field_name_suffix = (
        search_settings["analyzers"][analyzer.value]["index_fieldname_suffix"] or ""
    )
    return f"{model_field_name}{field_name_suffix}"
