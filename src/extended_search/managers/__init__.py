import inspect
import logging
from typing import Optional

from wagtail.search.index import get_indexed_models
from wagtail.search.query import SearchQuery

from extended_search.backends.query import Filtered
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


def get_query_for_model(model_class, query_str) -> SearchQuery:
    query = None
    for field_mapping in model_class.IndexManager.get_mapping():
        query_elements = model_class.IndexManager._get_search_query_from_mapping(
            query_str, model_class, field_mapping
        )
        if query_elements is not None:
            query = model_class.IndexManager._combine_queries(
                query,
                query_elements,
            )
    logger.debug(query)
    return query


def get_search_query(model_class, query_str, *args, **kwargs):
    """
    Generates a full query for a model class, by running query builder
    against the given model as well as all models with the given as a
    parent; each has it's own subquery using its own settings filtered by
    type, and all are joined together at the end.
    """
    extended_models = get_extended_models_with_indexmanager(model_class)
    # build full query for each extended model
    queries = []
    for sub_model_class in extended_models.values():
        query = get_query_for_model(sub_model_class, query_str)

        # filter so it only applies to "docs with that model anywhere in the contenttypes list"
        query = Filtered(
            query,
            filters=[
                (
                    "content_type",
                    "contains",
                    model_contenttype(sub_model_class),
                ),
            ],
        )
        queries.append(query)

    # build query for root model passed in to method, filter to exclude docs with contenttypes
    # matching any of the extended-models-with-dedicated-IM
    root_query = get_query_for_model(model_class, query_str)
    root_query = Filtered(
        root_query,
        filters=[
            (
                "content_type",
                "excludes",
                list(extended_models.keys()),
            ),
        ],
    )

    for q in queries:
        root_query |= q
    return root_query

def get_extended_models_with_indexmanager(model_class):
    # iterate indexed models extending the root model that have a dedicated IndexManager
    extended_model_classes = {}
    for indexed_model in get_indexed_models():
        if (
            indexed_model != model_class
            and model_class in inspect.getmro(indexed_model)
            and indexed_model.has_indexmanager_direct_inner_class()
        ):
            extended_model_classes[model_contenttype(indexed_model)] = indexed_model
    return extended_model_classes

def model_contenttype(model_class):
    return f"{model_class._meta.app_label}.{model_class.__name__}"
