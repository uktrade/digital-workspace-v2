from unittest.mock import call

import pytest
from wagtail.search.query import MATCH_NONE, PlainText

from content.models import ContentPage
from extended_search.backends.backend import (
    CustomSearchBackend,
    CustomSearchQueryCompiler,
    ExtendedSearchQueryCompiler,
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
        assert compiler.remapped_fields == compiler._remap_fields(compiler.fields)

        compiler = ExtendedSearchQueryCompiler(Person.objects.all(), query)
        assert compiler.remapped_fields == compiler._remap_fields(compiler.fields)

        compiler = ExtendedSearchQueryCompiler(Team.objects.all(), query)
        assert compiler.remapped_fields == compiler._remap_fields(compiler.fields)

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
        compiler._compile_query(query, "bar", 3.5)
        mock_parent.assert_called_once_with(query, "bar", 3.5)

        mock_parent.reset_mock()
        query = OnlyFields(PlainText("quid"), fields=["foo"])
        compiler = OnlyFieldSearchQueryCompiler(ContentPage.objects.all(), query)
        compiler._compile_query(query, "bar", 3.5)
        assert call(query, "bar", 3.5) not in mock_parent.calls()

    def test_compile_query_uses_remap_fields(self, mocker):
        mock_remap = mocker.patch(
            "extended_search.backends.backend.ExtendedSearchQueryCompiler._remap_fields"
        )
        query = OnlyFields(PlainText("quid"), fields=["foo"])
        compiler = OnlyFieldSearchQueryCompiler(ContentPage.objects.all(), query)
        compiler._compile_query(query, "bar", 3.5)
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
        compiler._compile_query(query, compiler.mapping.all_field_name, 8.3)
        mock_join_and_compile.assert_called_once_with(subquery, ["baz"], 8.3)
        mock_parent.assert_not_called()

        mock_parent.reset_mock()
        mock_join_and_compile.reset_mock()
        compiler._compile_query(query, "baz", 8.3)
        mock_join_and_compile.assert_not_called()
        mock_parent.assert_called_once_with(subquery, "baz", 8.3)

        mock_parent.reset_mock()
        mock_join_and_compile.reset_mock()
        compiler._compile_query(query, "foobar", 8.3)
        mock_join_and_compile.assert_not_called()
        mock_parent.assert_called_once_with(MATCH_NONE, "foobar", 8.3)


class TestCustomSearchBackend:
    def test_correct_mappings_and_backends_configured(self):
        assert CustomSearchBackend.query_compiler_class == CustomSearchQueryCompiler

    def test_custom_search_backend_used(self):
        assert SearchBackend == CustomSearchBackend
