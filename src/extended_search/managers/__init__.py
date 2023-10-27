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
    # print(f">>>>>> GET SUB QUERY FOR {model_class} <<<<<<")
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
    Uses the field mapping to derive the full nested SearchQuery
    """
    # print(f"------ GET QUERY FOR {model_class} -------")

    # iterate models
    #   check if indexmanager has been seen before, discard if so
    #   get fields defined on (novel) indexmanager
    #   generate query_part just for those fields
    # merge query_parts
    # profit

    # - OR -

    # # iterate models

    # extended_model_classes = []
    # for indexed_model in get_indexed_models():
    #     if model_class in inspect.getmro(indexed_model):
    #         extended_model_classes.append(model_class)

    # #   build query for each model

    # queries = []
    # for model_class in extended_model_classes:
    #     query = get_query_for_model(model_class, query_str)

    # #   add filter to query so it only applies to "docs with that model first in the contenttypes list"

    #     query.add_contenttype_is_filter(model_class)
    #     queries.append(query)

    # # merge queries

    # query = queries.pop()
    # for q in queries:
    #     query |= q
    # return query

    # - OR -

    def has_indexmanager_direct_inner_class(model_class):
        for attr in model_class.__dict__.values():
            if (
                inspect.isclass(attr)
                # and issubclass(attr, ModelIndexManager)
                and attr.__name__ == "IndexManager"
            ):
                return True
        return False

    def model_contenttype(model_class):
        return f"{model_class._meta.app_label}.{model_class.__name__}"

    # iterate indexed models extending the root model that have a dedicated IndexManager
    extended_model_classes = []
    for indexed_model in get_indexed_models():
        if (
            indexed_model != model_class
            and model_class in inspect.getmro(indexed_model)
            and has_indexmanager_direct_inner_class(indexed_model)
        ):
            extended_model_classes.append(indexed_model)
            # print(f"     @ ADDING {indexed_model}")
    extended_model_names = [model_contenttype(m) for m in extended_model_classes]

    # build query for root model passed in to method
    # add filter to root query to exclude docs with contenttypes matching any of the extended-models-with-dedicated-IM
    root_query = get_query_for_model(model_class, query_str)
    root_query = Filtered(
        root_query,
        filters=[
            (
                "content_type",
                "excludes",
                extended_model_names,
            ),
        ],
    )
    # print(f"     | ROOT QUERY FOR {model_class} |")

    # build full query for each extended model
    queries = []
    for sub_model_class in extended_model_classes:
        query = get_query_for_model(sub_model_class, query_str)
        # print(f"     ^ INNER QUERY FOR {sub_model_class} |")

        #   add filter to query so it only applies to "docs with that model anywhere in the contenttypes list"
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

    # merge all queries
    query = root_query
    for q in queries:
        query |= q
    return query


# Elasticsearch5SearchQueryCompiler reference
#
# get_content_type_filter() --> {"match": {"content_type": content_type}}
#
# def get_filters(self):
#     # Filter by content type
#     filters = [self.get_content_type_filter()]

#     # Apply filters from queryset
#     queryset_filters = self._get_filters_from_queryset()
#     if queryset_filters:
#         filters.append(queryset_filters)

#     return filters

# def get_query(self):
#     inner_query = self.get_inner_query()
#     filters = self.get_filters()

#     if len(filters) == 1:
#         return {
#             "bool": {
#                 "must": inner_query,
#                 "filter": filters[0],
#             }
#         }
#     elif len(filters) > 1:
#         return {
#             "bool": {
#                 "must": inner_query,
#                 "filter": filters,
#             }
#         }
#     else:
#         return inner_query
#
#
# Elasticsearch5Mapping reeference
#
# get_content_type() --> "wagtailcore.Page"
#
# get_all_content_types() --> ["myapp.MyPageModel", "wagtailcore.Page"]
