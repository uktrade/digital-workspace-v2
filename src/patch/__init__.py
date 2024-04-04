from wagtail.search import index

from extended_search.index import class_is_indexed, get_indexed_models


index.get_indexed_models = get_indexed_models
index.class_is_indexed = class_is_indexed


# @TODO Remove this once we can upstream the overrides
