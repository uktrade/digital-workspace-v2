from pathlib import Path

from django.core.management.base import BaseCommand
from wagtail.documents.models import Document
from wagtail.images.models import Image
from wagtailmedia.models import Media

from extended_search.index import get_indexed_models


# Path: src/extended_search/management/commands/create_index_fields_json.py
JSON_FILE = Path(__file__).parent / "indexed_models_and_fields.json"


def get_indexed_models_and_fields_dict():
    """
    Return a dictionary of indexed models and their fields
    Ignoring some models that we don't care about.
    """

    return {
        str(model): sorted([str(f) for f in model.get_search_fields()])
        for model in get_indexed_models()
        if model not in [Media, Document, Image]
        if model._meta.app_label != "testapp"
    }


class Command(BaseCommand):
    help = "Create test JSON containing indexed models and all of their fields"

    def handle(self, *args, **options):
        import json

        with open(JSON_FILE, "w") as f:
            json.dump(get_indexed_models_and_fields_dict(), f, indent=4)
