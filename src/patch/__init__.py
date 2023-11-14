from extended_search.index import get_indexed_models, class_is_indexed
from wagtail.search import index

index.get_indexed_models = get_indexed_models
index.class_is_indexed = class_is_indexed


# @TODO THIS WAS ALL CAM'S IDEA
