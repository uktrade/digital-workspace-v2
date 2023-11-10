import inspect
from unittest.mock import call

import pytest
from wagtail.search.backends.elasticsearch5 import Elasticsearch5SearchQueryCompiler
from wagtail.search.backends.elasticsearch6 import Field
from wagtail.search.index import RelatedFields, SearchField
from wagtail.search.query import MATCH_NONE, Fuzzy, Phrase, PlainText

from content.models import ContentPage
from extended_search.backends.backend import (
    BoostSearchQueryCompiler,
    CustomSearchBackend,
    CustomSearchMapping,
    CustomSearchQueryCompiler,
    ExtendedSearchQueryCompiler,
    FilteredSearchMapping,
    FilteredSearchQueryCompiler,
    NestedSearchQueryCompiler,
    OnlyFieldSearchQueryCompiler,
    SearchBackend,
)
from extended_search.backends.query import Filtered, Nested, OnlyFields
from peoplefinder.models import Person, Team


class TestExtendedSearchQueryCompiler:
    def test_remap_fields_works_the_same_as_parent_init(self):
        query = PlainText("quid")
        compiler = ExtendedSearchQueryCompiler(ContentPage.objects.all(), query)
        assert compiler._remap_fields(None) is None
        es5_compiler = Elasticsearch5SearchQueryCompiler(
            ContentPage.objects.all(), query
        )
        assert es5_compiler.remapped_fields == compiler._remap_fields(compiler.fields)

        compiler = ExtendedSearchQueryCompiler(Person.objects.all(), query)
        es5_compiler = Elasticsearch5SearchQueryCompiler(Person.objects.all(), query)
        assert es5_compiler.remapped_fields == compiler._remap_fields(compiler.fields)

        compiler = ExtendedSearchQueryCompiler(Team.objects.all(), query)
        es5_compiler = Elasticsearch5SearchQueryCompiler(Team.objects.all(), query)
        assert es5_compiler.remapped_fields == compiler._remap_fields(compiler.fields)

    def test_join_compile_queries_output_format_and_uses_compile_query(self, mocker):
        mock_compile = mocker.patch(
            "extended_search.backends.backend.ExtendedSearchQueryCompiler._compile_query",
            return_value="--FOO--",
        )
        query = PlainText("quid")
        compiler = ExtendedSearchQueryCompiler(ContentPage.objects.all(), query)
        result = compiler._join_and_compile_queries(query, ["bar"], 6.6)
        assert result == "--FOO--"
        mock_compile.assert_called_once_with(query, "bar", 6.6)

        mock_compile.reset_mock()
        result = compiler._join_and_compile_queries(query, ["bar", "baz", "bam"], 6.6)
        assert result == {"dis_max": {"queries": ["--FOO--", "--FOO--", "--FOO--"]}}
        mock_compile.assert_has_calls(
            [call(query, "bar", 6.6), call(query, "baz", 6.6), call(query, "bam", 6.6)]
        )
        assert mock_compile.call_count == 3

    @pytest.mark.xfail
    def test_get_inner_query_works_the_same_as_parent(self):
        assert True is False


class TestOnlyFieldSearchQueryCompiler:
    def test_compile_query_uses_parent_when_not_onlyfields(self, mocker):
        mock_parent = mocker.patch(
            "extended_search.backends.backend.ExtendedSearchQueryCompiler._compile_query"
        )
        query = PlainText("quid")
        compiler = OnlyFieldSearchQueryCompiler(ContentPage.objects.all(), query)
        field = Field("bar")
        compiler._compile_query(query, field, 3.5)
        mock_parent.assert_called_once_with(query, field, 3.5)

        mock_parent.reset_mock()
        query = OnlyFields(PlainText("quid"), fields=["foo"])
        compiler = OnlyFieldSearchQueryCompiler(ContentPage.objects.all(), query)
        compiler._compile_query(query, Field("bar"), 3.5)
        assert call(query, "bar", 3.5) not in mock_parent.calls()

    def test_compile_query_uses_remap_fields(self, mocker):
        mock_remap = mocker.patch(
            "extended_search.backends.backend.ExtendedSearchQueryCompiler._remap_fields"
        )
        query = OnlyFields(PlainText("quid"), fields=["foo"])
        compiler = OnlyFieldSearchQueryCompiler(ContentPage.objects.all(), query)
        compiler._compile_query(query, Field("bar"), 3.5)
        mock_remap.assert_called_once_with(["foo"])

    def test_compile_query_onlyfields_logic(self, mocker):
        mocker.patch(
            "extended_search.backends.backend.ExtendedSearchQueryCompiler._remap_fields",
            return_value=["baz"],
        )
        mock_parent = mocker.patch(
            "extended_search.backends.backend.ExtendedSearchQueryCompiler._compile_query"
        )
        mock_join_and_compile = mocker.patch(
            "extended_search.backends.backend.ExtendedSearchQueryCompiler._join_and_compile_queries"
        )
        subquery = PlainText("quid")
        query = OnlyFields(subquery, fields=["foo"])
        compiler = OnlyFieldSearchQueryCompiler(ContentPage.objects.all(), query)
        field = Field(compiler.mapping.all_field_name)
        compiler._compile_query(query, field, 8.3)
        mock_join_and_compile.assert_called_once_with(subquery, ["baz"], 8.3)
        mock_parent.assert_not_called()

        mock_parent.reset_mock()
        mock_join_and_compile.reset_mock()
        field = Field("baz")
        compiler._compile_query(query, field, 8.3)
        mock_join_and_compile.assert_not_called()
        mock_parent.assert_called_once_with(subquery, field, 8.3)

        mock_parent.reset_mock()
        mock_join_and_compile.reset_mock()
        field = Field("foobar")
        compiler._compile_query(query, field, 8.3)
        mock_join_and_compile.assert_not_called()
        mock_parent.assert_called_once_with(MATCH_NONE, field, 8.3)


class TestBoostSearchQueryCompiler:
    def test_compile_query_catches_all(self, mocker):
        mock_compile_fuzzy = mocker.patch(
            "extended_search.backends.backend.BoostSearchQueryCompiler._compile_fuzzy_query"
        )
        mock_compile_phrase = mocker.patch(
            "extended_search.backends.backend.BoostSearchQueryCompiler._compile_phrase_query"
        )
        query = PlainText("quid")
        field = Field("baz")
        compiler = BoostSearchQueryCompiler(ContentPage.objects.all(), query)
        compiler._compile_query(query, field, 443)
        mock_compile_fuzzy.assert_not_called()
        mock_compile_phrase.assert_not_called()
        query = Fuzzy("quid")
        compiler = BoostSearchQueryCompiler(ContentPage.objects.all(), query)
        compiler._compile_query(query, field, 443)
        mock_compile_fuzzy.assert_called_once_with(query, [field], 443)
        mock_compile_phrase.assert_not_called()
        mock_compile_fuzzy.reset_mock()
        query = Phrase("quid")
        compiler = BoostSearchQueryCompiler(ContentPage.objects.all(), query)
        compiler._compile_query(query, field, 443)
        mock_compile_fuzzy.assert_not_called()
        mock_compile_phrase.assert_called_once_with(query, [field], 443)

    def test_compile_fuzzy_query(self):
        query = Fuzzy("quid")
        field = Field("foo")
        compiler = BoostSearchQueryCompiler(ContentPage.objects.all(), query)
        parent_compiler = ExtendedSearchQueryCompiler(ContentPage.objects.all(), query)
        result = compiler._compile_fuzzy_query(query, [field], boost=1.0)
        assert result == parent_compiler._compile_fuzzy_query(query, [field])
        result = compiler._compile_fuzzy_query(query, [field], boost=3.0)
        assert "boost" in result["match"]["foo"]
        assert result["match"]["foo"]["boost"] == 3.0
        del result["match"]["foo"]["boost"]
        assert result == parent_compiler._compile_fuzzy_query(query, [field])
        field2 = Field("bar")
        result = compiler._compile_fuzzy_query(query, [field, field2], boost=47.0)
        assert result["multi_match"]["boost"] == 47.0

    def test_compile_phrase_query(self):
        query = Phrase("quid")
        field = Field("foo")
        compiler = BoostSearchQueryCompiler(ContentPage.objects.all(), query)
        parent_compiler = ExtendedSearchQueryCompiler(ContentPage.objects.all(), query)
        result = compiler._compile_phrase_query(query, [field], boost=1.0)
        assert result == parent_compiler._compile_phrase_query(query, [field])
        result = compiler._compile_phrase_query(query, [field], boost=3.0)
        assert "boost" in result["match_phrase"]["foo"]
        assert result["match_phrase"]["foo"]["boost"] == 3.0
        del result["match_phrase"]["foo"]["boost"]
        field2 = Field("bar")
        result = compiler._compile_phrase_query(query, [field, field2], boost=47.0)
        assert result["multi_match"]["boost"] == 47.0


class TestNestedSearchQueryCompiler:
    def test_get_searchable_fields(self):
        query = PlainText("quid")
        field = Field("baz")
        compiler = NestedSearchQueryCompiler(ContentPage.objects.all(), query)
        result = compiler.get_searchable_fields()
        for field in result:
            assert isinstance(field, SearchField) or isinstance(field, RelatedFields)
        count = 0
        for field in ContentPage.search_fields:
            if not (isinstance(field, SearchField) or isinstance(field, RelatedFields)):
                count += 1
        assert count > 0

    def test_compile_query_catches_nested(self, mocker):
        mock_compile_nested = mocker.patch(
            "extended_search.backends.backend.NestedSearchQueryCompiler._compile_nested_query"
        )
        query = PlainText("quid")
        field = Field("baz")
        compiler = NestedSearchQueryCompiler(ContentPage.objects.all(), query)
        compiler._compile_query(query, field, 443)
        mock_compile_nested.assert_not_called()
        query = Nested(query, path="content.content_page")
        compiler = NestedSearchQueryCompiler(ContentPage.objects.all(), query)
        compiler._compile_query(query, field, 443)
        mock_compile_nested.assert_called_once_with(query, [field], 443)

    def test_compile_nested_query(self):
        query = Nested(Phrase("quid"), path="content.content_page")
        field = Field("foo")
        compiler = NestedSearchQueryCompiler(ContentPage.objects.all(), query)
        parent_compiler = ExtendedSearchQueryCompiler(ContentPage.objects.all(), query)
        result = compiler._compile_nested_query(query, [field], boost=1.0)
        assert "nested" in result
        assert result["nested"]["path"] == query.path
        assert result["nested"]["query"] == parent_compiler._compile_query(
            query.subquery, [field]
        )


class TestFilteredSearchQueryCompiler:
    def test_compile_query_catches_filtered(self, mocker):
        mock_compile_filtered = mocker.patch(
            "extended_search.backends.backend.FilteredSearchQueryCompiler._compile_filtered_query"
        )
        query = PlainText("quid")
        field = Field("baz")
        compiler = FilteredSearchQueryCompiler(ContentPage.objects.all(), query)
        compiler._compile_query(query, field, 443)
        mock_compile_filtered.assert_not_called()
        query = Filtered(
            query, filters=[("content_type", "contains", "content.content_page")]
        )
        compiler = FilteredSearchQueryCompiler(ContentPage.objects.all(), query)
        compiler._compile_query(query, field, 443)
        mock_compile_filtered.assert_called_once_with(query, [field], 443)

    def test_compile_filtered_query(self, mocker):
        mock_process_lookup = mocker.patch(
            "extended_search.backends.backend.FilteredSearchQueryCompiler._process_lookup",
            return_value="foobar",
        )
        query = Filtered(
            Phrase("quid"),
            filters=[("content_type", "contains", "content.content_page")],
        )
        field = Field("foo")
        compiler = FilteredSearchQueryCompiler(ContentPage.objects.all(), query)
        parent_compiler = ExtendedSearchQueryCompiler(ContentPage.objects.all(), query)
        result = compiler._compile_filtered_query(query, [field], boost=1.0)
        mock_process_lookup.assert_called_once()
        assert "bool" in result
        assert result["bool"]["filter"] == "foobar"
        assert result["bool"]["must"] == parent_compiler._compile_query(
            query.subquery, [field]
        )
        query = Filtered(
            Phrase("quid"),
            filters=[
                ("content_type", "contains", "content.content_page"),
                ("another_field", "excludes", "anything"),
            ],
        )
        result = compiler._compile_filtered_query(query, [field], boost=1.0)
        assert result["bool"]["filter"] == ["foobar", "foobar"]

    def test_process_lookup(self, mocker):
        mock_parent = mocker.patch(
            "extended_search.backends.backend.ExtendedSearchQueryCompiler._process_lookup"
        )
        mocker.patch(
            "extended_search.backends.backend.Elasticsearch7Mapping.get_field_column_name",
            return_value="foobar",
        )
        field = Field("foo")
        query = PlainText("quid")
        compiler = FilteredSearchQueryCompiler(ContentPage.objects.all(), query)
        parent_compiler = ExtendedSearchQueryCompiler(ContentPage.objects.all(), query)
        result = compiler._process_lookup(field, "contains", 334)
        # mock_column_name.assert_called_once_with(field)  # @TODO commented out func call for now
        mock_parent.assert_not_called()
        assert result == {"match": {"foobar": 334}}
        result = compiler._process_lookup(field, "excludes", "bar")
        mock_parent.assert_not_called()
        assert result == {"bool": {"mustNot": {"terms": {"foobar": "bar"}}}}
        result = compiler._process_lookup(field, "gte", "bar")
        mock_parent.assert_called_with(field, "gte", "bar")
        assert result == parent_compiler._process_lookup(field, "gte", "bar")


class TestFilteredSearchMapping:
    def test_get_field_column_name(self, mocker):
        mock_parent = mocker.patch(
            "extended_search.backends.backend.Elasticsearch7Mapping.get_field_column_name"
        )
        map = FilteredSearchMapping(model=ContentPage)
        map.get_field_column_name("foo")
        mock_parent.assert_called_once()

        mock_parent.reset_mock()
        map.get_field_column_name(ContentPage._meta.fields[0])
        mock_parent.assert_called_once()

        mock_parent.reset_mock()
        result = map.get_field_column_name("content_type")
        mock_parent.assert_not_called()
        assert result == "content_type"


class TestCustomSearchBackend:
    def test_correct_mappings_and_backends_configured(self):
        assert CustomSearchBackend.query_compiler_class == CustomSearchQueryCompiler
        assert CustomSearchBackend.mapping_class == CustomSearchMapping
        assert ExtendedSearchQueryCompiler in inspect.getmro(CustomSearchQueryCompiler)
        assert BoostSearchQueryCompiler in inspect.getmro(CustomSearchQueryCompiler)
        assert FilteredSearchQueryCompiler in inspect.getmro(CustomSearchQueryCompiler)
        assert NestedSearchQueryCompiler in inspect.getmro(CustomSearchQueryCompiler)
        assert OnlyFieldSearchQueryCompiler in inspect.getmro(CustomSearchQueryCompiler)
        assert FilteredSearchMapping in inspect.getmro(CustomSearchMapping)

    def test_custom_search_backend_used(self):
        assert SearchBackend == CustomSearchBackend
