# Integration / functional output tests
import pytest
from django.conf import settings
from wagtail.search.backends import get_search_backend
from wagtail.search.index import AutocompleteField, SearchField

from content.models import ContentPage
from extended_search.query import Filtered
from extended_search.index import DWIndexedField as IndexedField
from extended_search.query_builder import CustomQueryBuilder
from extended_search.models import Setting
from extended_search.settings import SearchSettings, extended_search_settings
from news.models import NewsPage

existing_cp_fields = ContentPage.indexed_fields
existing_cp_search_fields = ContentPage.search_fields
existing_np_fields = NewsPage.indexed_fields
existing_np_search_fields = NewsPage.search_fields


class TestPerModelFieldOverrides:
    def get_search_mapping_for_updated_indexed_fields(
        self, model_class, indexed_fields, base_fields=None
    ):
        if base_fields is None:
            base_fields = []

        backend_name = settings.WAGTAILSEARCH_BACKENDS["default"]["BACKEND"]
        backend = get_search_backend(backend_name)

        model_class.processed_search_fields = {}
        model_class.indexed_fields = indexed_fields
        model_class.search_fields = base_fields
        index = backend.get_index_for_model(model_class)
        mapping_cls = index.mapping_class(model_class)

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
        content_mapping = self.get_search_mapping_for_updated_indexed_fields(
            ContentPage,
            [
                IndexedField(
                    "search_title",
                    search=True,
                    autocomplete=True,
                ),
            ],
        )
        news_mapping = self.get_search_mapping_for_updated_indexed_fields(
            NewsPage,
            [
                IndexedField(
                    "search_title",
                    search=True,
                ),
            ],
            ContentPage.search_fields,
        )

        assert (
            self.count_matching_search_autocomplete_fields(ContentPage, "search_title")
            == 2
        )
        assert (
            self.count_matching_search_autocomplete_fields(NewsPage, "search_title")
            == 1
        )

        assert "content_contentpage__search_title" in content_mapping["properties"]
        assert "news_newspage__search_title" in news_mapping["properties"]
        assert (
            "content_contentpage__search_title_edgengrams"
            in content_mapping["properties"]
        )
        assert (
            "content_contentpage__search_title_edgengrams"
            not in news_mapping["properties"]
        )
        assert (
            "news_newspage__search_title_edgengrams" not in news_mapping["properties"]
        )

    def test_maximal_subclass_overrides_minimal_baseclass(self):
        content_mapping = self.get_search_mapping_for_updated_indexed_fields(
            ContentPage,
            [
                IndexedField(
                    "search_title",
                    search=True,
                ),
            ],
        )
        news_mapping = self.get_search_mapping_for_updated_indexed_fields(
            NewsPage,
            [
                IndexedField(
                    "search_title",
                    search=True,
                    autocomplete=True,
                ),
            ],
            ContentPage.search_fields,
        )

        assert (
            self.count_matching_search_autocomplete_fields(ContentPage, "search_title")
            == 1
        )
        assert (
            self.count_matching_search_autocomplete_fields(NewsPage, "search_title")
            == 2
        )

        assert "content_contentpage__search_title" in content_mapping["properties"]
        assert "news_newspage__search_title" in news_mapping["properties"]
        assert (
            "content_contentpage__search_title_edgengrams"
            not in content_mapping["properties"]
        )
        assert (
            "content_contentpage__search_title_edgengrams" in news_mapping["properties"]
        )

    def test_subclass_overrides_boost(self):
        content_mapping = self.get_search_mapping_for_updated_indexed_fields(
            ContentPage,
            [
                IndexedField(
                    "search_title",
                    search=True,
                    boost=5.0,
                ),
            ],
        )
        news_mapping = self.get_search_mapping_for_updated_indexed_fields(
            NewsPage,
            [
                IndexedField(
                    "search_title",
                    search=True,
                    boost=10.0,
                ),
            ],
            ContentPage.search_fields,
        )

        # @TODO hopefully we can get a better boost indicator
        for field_name, field_details in content_mapping["properties"].items():
            if "search_title" in field_name:
                assert "_all_text_boost_10_0" not in field_details["copy_to"]
                assert "_all_text_boost_5_0" in field_details["copy_to"]

        for field_name, field_details in news_mapping["properties"].items():
            if "search_title" in field_name:
                assert "_all_text_boost_10_0" in field_details["copy_to"]
                assert "_all_text_boost_5_0" not in field_details["copy_to"]

    @pytest.mark.django_db
    def test_subclass_settings_overrides_work_only_on_subclass(self):
        self.get_search_mapping_for_updated_indexed_fields(
            ContentPage,
            [
                IndexedField(
                    "search_title",
                    search=True,
                    boost=5.0,
                ),
            ],
        )
        self.get_search_mapping_for_updated_indexed_fields(
            NewsPage,
            [
                IndexedField(
                    "search_title",
                    search=True,
                    boost=10.0,
                ),
            ],
            ContentPage.search_fields,
        )

        # @TODO this whole thing seems to not be working - is it the way I'm running the test?
        print(extended_search_settings)
        print(NewsPage.indexed_fields)
        print(NewsPage.get_search_fields())

        content_field_key = "content.contentpage.search_title"
        news_field_key = "news.newspage.search_title"

        assert (
            extended_search_settings["boost_parts"]["fields"][content_field_key] == 5.0
        )
        assert extended_search_settings["boost_parts"]["fields"][news_field_key] == 10.0
        instance = SearchSettings()
        instance.initialise_db_dict()
        Setting.objects.create(key=news_field_key, value=100.5)
        assert Setting.objects.all().count() == 1
        instance.initialise_db_dict()
        assert extended_search_settings[news_field_key] == 100.5

    def find_filter(self, query):
        if isinstance(query, Filtered):
            self.filter_parts.append(query)
            return query
        if hasattr(query, "subqueries"):
            subs = []
            for q in query.subqueries:
                subs.append(self.find_filter(q))
            return subs
        return query.subquery

    @pytest.mark.django_db
    def test_generated_search_applies_baseclass_and_subclass_filters(self):
        ContentPage.indexed_fields = existing_cp_fields
        ContentPage.search_fields = existing_cp_search_fields
        NewsPage.indexed_fields = existing_np_fields
        NewsPage.search_fields = existing_np_search_fields

        query = CustomQueryBuilder.get_search_query(ContentPage, "foo")

        extended_models = (
            CustomQueryBuilder.get_extended_models_with_unique_indexed_fields(
                ContentPage
            )
        )

        self.filter_parts = []
        self.find_filter(query)

        num_excludes = 0
        assert len(self.filter_parts) == len(extended_models) + 1
        for r in self.filter_parts:
            field, lookup, value = r.filters[0]
            assert field == "content_type"
            assert lookup in ("contains", "excludes")
            if lookup == "excludes":
                num_excludes += 1
                assert (
                    f"{ContentPage._meta.app_label}.{ContentPage.__name__}" not in value
                )
                for model in extended_models:
                    assert f"{model._meta.app_label}.{model.__name__}" in value
            else:
                assert value in [
                    f"{model._meta.app_label}.{model.__name__}"
                    for model in extended_models
                ]
        assert num_excludes == 1
