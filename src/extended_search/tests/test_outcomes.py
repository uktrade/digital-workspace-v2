# Integration / functional output tests
import pytest
from content.models import ContentPage
from django.conf import settings
from extended_search.fields import IndexedField
from news.models import NewsPage
from wagtail.search.backends import get_search_backend
from wagtail.search.index import AutocompleteField, SearchField


class TestPerModelFieldOverrides:
    @pytest.fixture()
    def backend(self):
        backend_name = settings.WAGTAILSEARCH_BACKENDS["default"]["BACKEND"]
        self.backend = get_search_backend(backend_name)

    def update_and_get_mapping_from_model_fields(
        self, model_class, fields, base_fields=None
    ):
        if base_fields is None:
            base_fields = []

        model_class.IndexManager.fields = fields
        # model_class.search_fields = base_fields + model_class.IndexManager()
        index = self.backend.get_index_for_model(model_class)
        mapping_cls = index.mapping_class(model_class)
        return mapping_cls.get_mapping()

    def count_matching_search_autocomplete_fields(self, model_class, name):
        count = 0
        for field in model_class.search_fields:
            if getattr(field, "model_field_name", None) == name and (
                isinstance(field, SearchField) or isinstance(field, AutocompleteField)
            ):
                count += 1
        return count

    def test_minimal_subclass_overrides_maximal_baseclass(self, backend):
        content_mapping = self.update_and_get_mapping_from_model_fields(
            ContentPage,
            [
                IndexedField(
                    "search_title",
                    tokenized=True,
                    autocomplete=True,
                ),
            ],
        )
        news_mapping = self.update_and_get_mapping_from_model_fields(
            NewsPage,
            [
                IndexedField(
                    "search_title",
                    tokenized=True,
                ),
            ],
            ContentPage.search_fields,
        )
        print(">>>", ContentPage.search_fields)
        print(content_mapping)
        print(">>>>>", NewsPage.search_fields)
        print(news_mapping)
        assert (
            self.count_matching_search_autocomplete_fields(ContentPage, "search_title")
            == 2
        )
        assert (
            self.count_matching_search_autocomplete_fields(NewsPage, "search_title")
            == 1
        )

        assert "content_contentpage__search_title" in content_mapping["properties"]
        assert "content_contentpage__search_title" in news_mapping["properties"]
        assert (
            "content_contentpage__search_title_edgengrams"
            in content_mapping["properties"]
        )
        assert (
            "content_contentpage__search_title_edgengrams"
            not in news_mapping["properties"]
        )

    def test_maximal_subclass_overrides_minimal_baseclass(self, backend):
        content_mapping = self.update_and_get_mapping_from_model_fields(
            ContentPage,
            [
                IndexedField(
                    "search_title",
                    tokenized=True,
                ),
            ],
        )
        news_mapping = self.update_and_get_mapping_from_model_fields(
            NewsPage,
            [
                IndexedField(
                    "search_title",
                    tokenized=True,
                    autocomplete=True,
                ),
            ],
        )

        assert len(ContentPage.search_fields) == 1
        assert len(NewsPage.search_fields) == 2

        assert "content_contentpage__search_title" in content_mapping["properties"]
        assert "content_contentpage__search_title" in news_mapping["properties"]
        assert (
            "content_contentpage__search_title_edgengrams"
            not in content_mapping["properties"]
        )
        assert (
            "content_contentpage__search_title_edgengrams" in news_mapping["properties"]
        )

    def test_subclass_overrides_boost(self, backend):
        content_mapping = self.update_and_get_mapping_from_model_fields(
            ContentPage,
            [
                IndexedField(
                    "search_title",
                    tokenized=True,
                    boost=5.0,
                ),
            ],
        )
        news_mapping = self.update_and_get_mapping_from_model_fields(
            NewsPage,
            [
                IndexedField(
                    "search_title",
                    tokenized=True,
                    boost=10.0,
                ),
            ],
        )

        assert "content_contentpage__search_title" in content_mapping["properties"]
        assert "content_contentpage__search_title" in news_mapping["properties"]
        assert (
            "boost"
            not in content_mapping["properties"]["content_contentpage__search_title"]
        )
        assert (
            "boost" in news_mapping["properties"]["content_contentpage__search_title"]
        )
        raise AssertionError()

    def test_subclass_settings_overrides_work_only_on_subclass(self, backend):
        self.update_and_get_mapping_from_model_fields(
            ContentPage,
            [
                IndexedField(
                    "search_title",
                    tokenized=True,
                    boost=5.0,
                ),
            ],
        )
        self.update_and_get_mapping_from_model_fields(
            NewsPage,
            [
                IndexedField(
                    "search_title",
                    tokenized=True,
                    boost=10.0,
                ),
            ],
        )
        raise AssertionError()

    def test_generated_search_applies_basclass_and_subclass_filters(self, backend):
        raise AssertionError()
