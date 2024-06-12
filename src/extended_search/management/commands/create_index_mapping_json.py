from pathlib import Path

from django.core.management.base import BaseCommand
from wagtail.documents.models import Document
from wagtail.images.models import Image
from wagtail.search.backends import get_search_backend
from wagtailmedia.models import Media

from extended_search.index import get_indexed_models


# Path: src/extended_search/management/commands/create_index_fields_json.py
JSON_FILE = Path(__file__).parent / "indexed_mapping.json"


def get_sorted_mapping(search_backend, model):
    mapping = search_backend.mapping_class(model).get_mapping()

    def sort_dict(d):
        sorted_dict = dict(sorted(d.items()))
        for k, v in d.items():
            if isinstance(v, dict):
                sorted_dict[k] = sort_dict(v)
            else:
                sorted_dict[k] = v
        return sorted_dict

    return sort_dict(mapping)


def get_indexed_mapping_dict():
    """
    Return a dictionary of indexed models and their fields
    Ignoring some models that we don't care about.
    """
    search_backend = get_search_backend()

    return {
        str(model): get_sorted_mapping(search_backend, model)
        for model in get_indexed_models()
        # if model not in [Media, Document, Image]
        if model._meta.app_label != "testapp"
    }


class Command(BaseCommand):
    help = "Create test JSON containing the mapping for all indexed models"

    def handle(self, *args, **options):
        import json

        with open(JSON_FILE, "w") as f:
            json.dump(get_indexed_mapping_dict(), f, indent=4)
