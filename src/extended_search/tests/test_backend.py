from unittest.mock import call

import inspect
import pytest
from wagtail.search.backends.elasticsearch5 import Elasticsearch5SearchQueryCompiler
from wagtail.search.backends.elasticsearch6 import Field
from wagtail.search.query import MATCH_NONE, PlainText

from content.models import ContentPage
from extended_search.backends.backend import (
    BoostSearchQueryCompiler,
    CustomSearchBackend,
    CustomSearchQueryCompiler,
    ExtendedSearchQueryCompiler,
    FilteredSearchMapping,
    FilteredSearchQueryCompiler,
    NestedSearchQueryCompiler,
    OnlyFieldSearchQueryCompiler,
    SearchBackend,
)
from extended_search.backends.query import OnlyFields
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
        raise AssertionError()

    def test_compile_fuzzy_query(self):
        raise AssertionError()

    def test_compile_phrase_query(self):
        raise AssertionError()


class TestNestedSearchQueryCompiler:
    def test_get_searchable_fields(self):
        raise AssertionError()

    def test_compile_query_catches_nested(self, mocker):
        raise AssertionError()

    def test_compile_nested_query(self):
        raise AssertionError()


class TestFilteredSearchQueryCompiler:
    def test_compile_query_catches_filtered(self, mocker):
        raise AssertionError()

    def test_compile_filtered_query(self):
        raise AssertionError()

    def test_process_lookup(self):
        raise AssertionError()


class TestFilteredSearchMapping:
    def test_get_field_column_name(self, mocker):
        raise AssertionError()


class TestCustomSearchBackend:
    def test_correct_mappings_and_backends_configured(self):
        assert CustomSearchBackend.query_compiler_class == CustomSearchQueryCompiler
        assert CustomSearchBackend.mapping_class == FilteredSearchMapping
        assert ExtendedSearchQueryCompiler in inspect.getmro(CustomSearchQueryCompiler)
        assert BoostSearchQueryCompiler in inspect.getmro(CustomSearchQueryCompiler)
        assert FilteredSearchQueryCompiler in inspect.getmro(CustomSearchQueryCompiler)
        assert NestedSearchQueryCompiler in inspect.getmro(CustomSearchQueryCompiler)
        assert OnlyFieldSearchQueryCompiler in inspect.getmro(CustomSearchQueryCompiler)

    def test_custom_search_backend_used(self):
        assert SearchBackend == CustomSearchBackend
