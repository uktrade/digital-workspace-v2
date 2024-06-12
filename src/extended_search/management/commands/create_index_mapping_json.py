from pathlib import Path

from django.core.management.base import BaseCommand
from wagtail.search.backends import get_search_backend

from extended_search.index import get_indexed_models


# Path: src/extended_search/management/commands/create_index_fields_json.py
JSON_FILE = Path(__file__).parent / "indexed_mapping.json"


def get_indexed_mapping_dict():
    """
    Return a dictionary of indexed models and their fields
    Ignoring some models that we don't care about.
    """

    search_backend = get_search_backend()

    return {
        str(model): search_backend.mapping_class(model).get_mapping()
        for model in get_indexed_models()
    }


class Command(BaseCommand):
    help = "Create test JSON containing the mapping for all indexed models"

    def handle(self, *args, **options):
        import json

        with open(JSON_FILE, "w") as f:
            json.dump(get_indexed_mapping_dict(), f, indent=4)
