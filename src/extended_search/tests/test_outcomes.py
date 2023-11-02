# Integration / functional output tests
import pytest
from django.conf import settings

from wagtail.search.backends import get_search_backend
from wagtail.search.index import AutocompleteField, SearchField
from wagtail.search.query import Or

from content.models import ContentPage
from extended_search.backends.query import Filtered
from extended_search.fields import IndexedField
from extended_search.models import Setting
from extended_search.managers import (
    get_search_query,
    get_extended_models_with_indexmanager,
)
from extended_search.settings import SearchSettings, extended_search_settings
from news.models import NewsPage


existing_cp_fields = ContentPage.IndexManager.fields
existing_cp_search_fields = ContentPage.search_fields
existing_np_fields = NewsPage.IndexManager.fields
existing_np_search_fields = NewsPage.search_fields


class TestPerModelFieldOverrides:
    def update_and_get_mapping_from_model_fields(
        self, model_class, fields, base_fields=None
    ):
        if base_fields is None:
            base_fields = []

        backend_name = settings.WAGTAILSEARCH_BACKENDS["default"]["BACKEND"]
        backend = get_search_backend(backend_name)

        model_class.IndexManager.fields = fields
        model_class.search_fields = base_fields + model_class.IndexManager()
        index = backend.get_index_for_model(model_class)
        mapping_cls = index.mapping_class(model_class)
        return mapping_cls.get_mapping()

    def count_matching_search_autocomplete_fields(self, model_class, name):
        count = 0
        for field in model_class.search_fields:
            if field.field_name == name and (
                isinstance(field, SearchField) or isinstance(field, AutocompleteField)
            ):
                count += 1
        return count

    @pytest.mark.xfail
    def test_updated_outcomes(self):
        # All these tests are a bit funky because our overrides aren't working
        # too nicely. Update them all once we've fixed this
        ...

    def test_minimal_subclass_overrides_maximal_baseclass(self):
        content_mapping = self.update_and_get_mapping_from_model_fields(
            ContentPage,
            [
                IndexedField(
                    "search_title",
                    search=True,
                    autocomplete=True,
                ),
            ],
        )
        news_mapping = self.update_and_get_mapping_from_model_fields(
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
            == 3  #  @TODO this ought to be 1 when we run the overrides properly
        )

        assert "content_contentpage__search_title" in content_mapping["properties"]
        assert "news_newspage__search_title" in news_mapping["properties"]  #  @TODO
        assert (
            "content_contentpage__search_title_edgengrams"
            in content_mapping["properties"]
        )
        # assert (
        #     "content_contentpage__search_title_edgengrams"
        #     not in news_mapping["properties"]
        # ) @TODO

    def test_maximal_subclass_overrides_minimal_baseclass(self):
        content_mapping = self.update_and_get_mapping_from_model_fields(
            ContentPage,
            [
                IndexedField(
                    "search_title",
                    search=True,
                ),
            ],
        )
        news_mapping = self.update_and_get_mapping_from_model_fields(
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
            == 3  # @TODO this ought to be 2 when we run the overrides properly
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
        content_mapping = self.update_and_get_mapping_from_model_fields(
            ContentPage,
            [
                IndexedField(
                    "search_title",
                    search=True,
                    boost=5.0,
                ),
            ],
        )
        news_mapping = self.update_and_get_mapping_from_model_fields(
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
        assert "_all_text_boost_5_0" in content_mapping["properties"]
        assert "_all_text_boost_10_0" not in content_mapping["properties"]
        assert "_all_text_boost_5_0" not in news_mapping["properties"]
        assert "_all_text_boost_10_0" in news_mapping["properties"]

    @pytest.mark.django_db
    @pytest.mark.xfail
    def test_subclass_settings_overrides_work_only_on_subclass(self):
        content_mapping = self.update_and_get_mapping_from_model_fields(
            ContentPage,
            [
                IndexedField(
                    "search_title",
                    search=True,
                    boost=5.0,
                ),
            ],
        )
        news_mapping = self.update_and_get_mapping_from_model_fields(
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

        content_field_key = "boost_parts__fields__content.contentpage.search_title"
        news_field_key = "boost_parts__fields__news.newspage.search_title"

        assert extended_search_settings[content_field_key] == 5.0
        assert extended_search_settings[news_field_key] == 10.0
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
        ContentPage.IndexManager.fields = existing_cp_fields
        ContentPage.search_fields = existing_cp_search_fields
        NewsPage.IndexManager.fields = existing_np_fields
        NewsPage.search_fields = existing_np_search_fields

        query = get_search_query(ContentPage, "foo")
        extended_models = get_extended_models_with_indexmanager(ContentPage)

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
                for name in extended_models.keys():
                    assert name in value
            else:
                assert value in extended_models.keys()
        assert num_excludes == 1
