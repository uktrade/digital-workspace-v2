# Integration / functional output tests
import pytest
from django.conf import settings
from wagtail.search.backends import get_search_backend
from wagtail.search.index import AutocompleteField, SearchField

from extended_search.index import DWIndexedField as IndexedField
from extended_search.models import Setting
from extended_search.settings import SearchSettings, settings_singleton
from testapp.models import ChildModel, IndexedModel


class TestPerModelFieldOverrides:
    def get_search_mapping_for_updated_indexed_fields(
        self, model_class, indexed_fields, base_fields=None
    ):
        if base_fields is None:
            base_fields = []

        backend_name = settings.WAGTAILSEARCH_BACKENDS["default"]["BACKEND"]
        backend = get_search_backend(backend_name)

        model_class.processed_search_fields = {}  # kills get_search_fields cache
        model_class.indexed_fields = indexed_fields
        model_class.search_fields = base_fields
        index = backend.get_index_for_model(model_class)
        mapping_cls = index.mapping_class(model_class)

        settings_singleton.initialise_field_dict()

        return mapping_cls.get_mapping()

    def count_matching_search_autocomplete_fields(self, model_class, name):
        count = 0
        for field in model_class.get_search_fields(ignore_cache=True):
            if name in field.field_name and (  # catch variants like "_explicit"
                isinstance(field, SearchField) or isinstance(field, AutocompleteField)
            ):
                count += 1
        return count

    def test_minimal_subclass_overrides_maximal_baseclass(self):
        parent_mapping = self.get_search_mapping_for_updated_indexed_fields(
            IndexedModel,
            [
                IndexedField(
                    "title",
                    search=True,
                    autocomplete=True,
                ),
            ],
        )
        child_mapping = self.get_search_mapping_for_updated_indexed_fields(
            ChildModel,
            [
                IndexedField(
                    "title",
                    search=True,
                ),
            ],
            IndexedModel.search_fields,
        )

        assert (
            self.count_matching_search_autocomplete_fields(IndexedModel, "title") == 2
        )
        assert self.count_matching_search_autocomplete_fields(ChildModel, "title") == 1

        assert "testapp_indexedmodel__title" in parent_mapping["properties"]
        assert "testapp_childmodel__title" in child_mapping["properties"]
        assert "testapp_indexedmodel__title_edgengrams" in parent_mapping["properties"]
        assert (
            "testapp_indexedmodel__title_edgengrams" not in child_mapping["properties"]
        )
        assert "testapp_childmodel__title_edgengrams" not in child_mapping["properties"]

    def test_maximal_subclass_overrides_minimal_baseclass(self):
        parent_mapping = self.get_search_mapping_for_updated_indexed_fields(
            IndexedModel,
            [
                IndexedField(
                    "title",
                    search=True,
                ),
            ],
        )
        child_mapping = self.get_search_mapping_for_updated_indexed_fields(
            ChildModel,
            [
                IndexedField(
                    "title",
                    search=True,
                    autocomplete=True,
                ),
            ],
            IndexedModel.search_fields,
        )

        assert (
            self.count_matching_search_autocomplete_fields(IndexedModel, "title") == 1
        )
        assert self.count_matching_search_autocomplete_fields(ChildModel, "title") == 2

        assert "testapp_indexedmodel__title" in parent_mapping["properties"]
        assert "testapp_childmodel__title" in child_mapping["properties"]
        assert (
            "testapp_indexedmodel__title_edgengrams" not in parent_mapping["properties"]
        )
        assert "testapp_childmodel__title_edgengrams" in child_mapping["properties"]

    def test_subclass_overrides_boost(self):
        parent_mapping = self.get_search_mapping_for_updated_indexed_fields(
            IndexedModel,
            [
                IndexedField(
                    "title",
                    search=True,
                    boost=5.0,
                ),
            ],
        )
        child_mapping = self.get_search_mapping_for_updated_indexed_fields(
            ChildModel,
            [
                IndexedField(
                    "title",
                    search=True,
                    boost=10.0,
                ),
            ],
            IndexedModel.search_fields,
        )

        # Not the best boost indicator - but it works
        for field_name, field_details in parent_mapping["properties"].items():
            if "title" in field_name:
                assert "_all_text_boost_10_0" not in field_details["copy_to"]
                assert "_all_text_boost_5_0" in field_details["copy_to"]

        for field_name, field_details in child_mapping["properties"].items():
            if "title" in field_name:
                assert "_all_text_boost_10_0" in field_details["copy_to"]
                assert "_all_text_boost_5_0" not in field_details["copy_to"]

    @pytest.mark.django_db
    def test_subclass_settings_overrides_work_only_on_subclass(self):
        self.get_search_mapping_for_updated_indexed_fields(
            IndexedModel,
            [
                IndexedField(
                    "title",
                    search=True,
                    boost=5.0,
                ),
            ],
        )
        self.get_search_mapping_for_updated_indexed_fields(
            ChildModel,
            [
                IndexedField(
                    "title",
                    search=True,
                    boost=10.0,
                ),
            ],
            IndexedModel.search_fields,
        )
        search_settings = settings_singleton.to_dict()

        parent_field_key = "testapp.indexedmodel.title"
        child_field_key = "testapp.childmodel.title"

        assert search_settings["boost_parts"]["fields"][parent_field_key] == 5.0
        assert search_settings["boost_parts"]["fields"][child_field_key] == 10.0

        instance = SearchSettings()
        instance.initialise_db_dict()
        Setting.objects.create(
            key=f"boost_parts__fields__{child_field_key}", value=100.5
        )
        assert Setting.objects.all().count() == 1
        instance.initialise_db_dict()

        search_settings = settings_singleton.to_dict()
        assert search_settings["boost_parts"]["fields"][child_field_key] == str(100.5)
