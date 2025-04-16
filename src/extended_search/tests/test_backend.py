import inspect
from unittest.mock import call

from wagtail.search.backends.elasticsearch7 import (
    Elasticsearch7SearchQueryCompiler,
    Field,
)
from wagtail.search.index import RelatedFields, SearchField
from wagtail.search.query import (
    MATCH_NONE,
    Fuzzy,
    MatchAll,
    Not,
    Phrase,
    PlainText,
    SearchQuery,
)

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
from extended_search.query import Filtered, Nested, OnlyFields
from peoplefinder.models import Person, Team


class TestExtendedSearchQueryCompiler:
    def test_remap_fields_works_the_same_as_parent_init(self):
        query = PlainText("quid")
        compiler = ExtendedSearchQueryCompiler(ContentPage.objects.all(), query)
        es7_compiler = Elasticsearch7SearchQueryCompiler(
            ContentPage.objects.all(), query
        )
        assert [rf.field_name for rf in es7_compiler.remapped_fields] == [
            rf.field_name for rf in compiler._remap_fields(compiler.fields)
        ]

        compiler = ExtendedSearchQueryCompiler(Person.objects.all(), query)
        es7_compiler = Elasticsearch7SearchQueryCompiler(Person.objects.all(), query)
        assert [rf.field_name for rf in es7_compiler.remapped_fields] == [
            rf.field_name for rf in compiler._remap_fields(compiler.fields)
        ]

        compiler = ExtendedSearchQueryCompiler(Team.objects.all(), query)
        es7_compiler = Elasticsearch7SearchQueryCompiler(Team.objects.all(), query)
        assert [rf.field_name for rf in es7_compiler.remapped_fields] == [
            rf.field_name for rf in compiler._remap_fields(compiler.fields)
        ]

    def test_remap_fields_handles_parent_relations(self, mocker):
        field1 = mocker.Mock(field_name="--field-1--")
        field2 = mocker.Mock(field_name="--field-2--")
        field3 = mocker.Mock(field_name="--field-3--")
        mocker.patch(
            "wagtail.search.backends.elasticsearch7.Elasticsearch7SearchQueryCompiler.get_searchable_fields",
            return_value=[
                field1,
                field2,
                field3,
            ],
        )
        mock_get_column_name = mocker.patch(
            "extended_search.backends.backend.Elasticsearch7Mapping.get_field_column_name",
            return_value="--column-name--",
        )
        query = PlainText("foo")
        compiler = ExtendedSearchQueryCompiler(ContentPage.objects.all(), query)

        results = compiler._remap_fields(
            [
                "--field-1--.--related-field--",
                "--field-3--.--some-other-field--.--another-relation--",
            ]
        )
        mock_get_column_name.assert_has_calls([call(field1), call(field3)])
        assert [f.field_name for f in results] == [
            "--column-name--.--related-field--",
            "--column-name--.--some-other-field--.--another-relation--",
        ]

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

    def test_get_inner_query_works_the_same_as_parent(self, mocker):
        query = PlainText("foo")
        compiler = ExtendedSearchQueryCompiler(ContentPage.objects.all(), query)
        compiler_es7 = Elasticsearch7SearchQueryCompiler(
            ContentPage.objects.all(), query
        )
        compiler_es7.mapping.all_field_name = None
        mock_compile_plaintext = mocker.patch(
            "extended_search.backends.backend.ExtendedSearchQueryCompiler._compile_plaintext_query",
        )
        mock_compile_plaintext_es7 = mocker.patch(
            "wagtail.search.backends.elasticsearch7.Elasticsearch7SearchQueryCompiler._compile_plaintext_query",
        )
        mock_compile_phrase = mocker.patch(
            "extended_search.backends.backend.ExtendedSearchQueryCompiler._compile_phrase_query",
        )
        mock_compile_phrase_es7 = mocker.patch(
            "wagtail.search.backends.elasticsearch7.Elasticsearch7SearchQueryCompiler._compile_phrase_query",
        )
        mock_compile_fuzzy = mocker.patch(
            "extended_search.backends.backend.ExtendedSearchQueryCompiler._compile_fuzzy_query",
        )
        mock_compile_fuzzy_es7 = mocker.patch(
            "wagtail.search.backends.elasticsearch7.Elasticsearch7SearchQueryCompiler._compile_fuzzy_query",
        )
        mock_compile = mocker.patch(
            "extended_search.backends.backend.ExtendedSearchQueryCompiler._compile_query",
        )
        mock_compile_es7 = mocker.patch(
            "wagtail.search.backends.elasticsearch7.Elasticsearch7SearchQueryCompiler._compile_query",
        )
        mock_join_and_compile = mocker.patch(
            "extended_search.backends.backend.ExtendedSearchQueryCompiler._join_and_compile_queries",
        )

        compiler.remapped_fields = compiler_es7.remapped_fields = []
        assert compiler.get_inner_query() == {"bool": {"mustNot": {"match_all": {}}}}
        mock_compile_plaintext.assert_not_called()
        mock_compile_phrase.assert_not_called()
        mock_compile_fuzzy.assert_not_called()
        mock_compile.assert_not_called()
        mock_join_and_compile.assert_not_called()

        compiler.remapped_fields = compiler_es7.remapped_fields = [
            Field("--field-1--"),
        ]
        assert compiler.get_inner_query() == mock_compile_plaintext.return_value
        assert compiler_es7.get_inner_query() == mock_compile_plaintext_es7.return_value
        mock_compile_plaintext.assert_called_once()
        mock_compile_phrase.assert_not_called()
        mock_compile_fuzzy.assert_not_called()
        mock_compile.assert_not_called()
        mock_join_and_compile.assert_not_called()

        mock_compile_plaintext.reset_mock()
        query = Phrase("foo")
        compiler = ExtendedSearchQueryCompiler(ContentPage.objects.all(), query)
        compiler_es7 = Elasticsearch7SearchQueryCompiler(
            ContentPage.objects.all(), query
        )
        compiler.remapped_fields = compiler_es7.remapped_fields = [
            Field("--field-1--"),
        ]
        assert compiler.get_inner_query() == mock_compile_phrase.return_value
        assert compiler_es7.get_inner_query() == mock_compile_phrase_es7.return_value
        mock_compile_plaintext.assert_not_called()
        mock_compile_phrase.assert_called_once()
        mock_compile_fuzzy.assert_not_called()
        mock_compile.assert_not_called()
        mock_join_and_compile.assert_not_called()

        mock_compile_phrase.reset_mock()
        query = MatchAll()
        compiler = ExtendedSearchQueryCompiler(ContentPage.objects.all(), query)
        compiler_es7 = Elasticsearch7SearchQueryCompiler(
            ContentPage.objects.all(), query
        )
        compiler.remapped_fields = compiler_es7.remapped_fields = [
            Field("--field-1--"),
        ]
        assert compiler.get_inner_query() == {"match_all": {}}
        assert compiler_es7.get_inner_query() == {"match_all": {}}
        mock_compile_plaintext.assert_not_called()
        mock_compile_phrase.assert_not_called()
        mock_compile_fuzzy.assert_not_called()
        mock_compile.assert_not_called()
        mock_join_and_compile.assert_not_called()

        query = Fuzzy("foo")
        compiler = ExtendedSearchQueryCompiler(ContentPage.objects.all(), query)
        compiler_es7 = Elasticsearch7SearchQueryCompiler(
            ContentPage.objects.all(), query
        )
        compiler.remapped_fields = compiler_es7.remapped_fields = [
            Field("--field-1--"),
        ]
        assert compiler.get_inner_query() == mock_compile_fuzzy.return_value
        assert compiler_es7.get_inner_query() == mock_compile_fuzzy_es7.return_value
        mock_compile_plaintext.assert_not_called()
        mock_compile_phrase.assert_not_called()
        mock_compile_fuzzy.assert_called_once()
        mock_compile.assert_not_called()
        mock_join_and_compile.assert_not_called()

        mock_compile_fuzzy.reset_mock()
        query = Not(PlainText("foo"))
        compiler = ExtendedSearchQueryCompiler(ContentPage.objects.all(), query)
        compiler_es7 = Elasticsearch7SearchQueryCompiler(
            ContentPage.objects.all(), query
        )
        compiler.remapped_fields = compiler_es7.remapped_fields = [
            Field("--field-1--"),
        ]
        assert compiler.get_inner_query() == {
            "bool": {"mustNot": [mock_compile.return_value]}
        }
        assert compiler_es7.get_inner_query() == {
            "bool": {"mustNot": [mock_compile_es7.return_value]}
        }
        mock_compile_plaintext.assert_not_called()
        mock_compile_phrase.assert_not_called()
        mock_compile_fuzzy.assert_not_called()
        mock_compile.assert_called_once()
        mock_join_and_compile.assert_not_called()

        mock_compile.reset_mock()
        query = SearchQuery()
        compiler = ExtendedSearchQueryCompiler(ContentPage.objects.all(), query)
        compiler_es7 = Elasticsearch7SearchQueryCompiler(
            ContentPage.objects.all(), query
        )
        compiler.remapped_fields = compiler_es7.remapped_fields = [
            Field("--field-1--"),
        ]
        assert compiler.get_inner_query() == mock_join_and_compile.return_value
        assert compiler_es7.get_inner_query() == mock_compile_es7.return_value
        mock_compile_plaintext.assert_not_called()
        mock_compile_phrase.assert_not_called()
        mock_compile_fuzzy.assert_not_called()
        mock_compile.assert_not_called()
        mock_join_and_compile.assert_called_once()

        mock_join_and_compile.reset_mock()
        compiler.remapped_fields = compiler_es7.remapped_fields = [
            Field("--field-1--"),
            Field("--field-2--"),
        ]
        assert compiler.get_inner_query() == mock_join_and_compile.return_value
        assert compiler_es7.get_inner_query() == {
            "dis_max": {
                "queries": [
                    mock_compile_es7.return_value,
                    mock_compile_es7.return_value,
                ]
            }
        }
        mock_compile_plaintext.assert_not_called()
        mock_compile_phrase.assert_not_called()
        mock_compile_fuzzy.assert_not_called()
        mock_compile.assert_not_called()
        mock_join_and_compile.assert_called_once()


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
        query = OnlyFields(PlainText("quid"), fields=["foo"], only_model=ContentPage)
        compiler = OnlyFieldSearchQueryCompiler(ContentPage.objects.all(), query)
        compiler._compile_query(query, Field("bar"), 3.5)
        assert call(query, "bar", 3.5) not in mock_parent.calls()

    def test_compile_query_uses_remap_fields(self, mocker):
        mock_remap = mocker.patch(
            "extended_search.backends.backend.ExtendedSearchQueryCompiler._remap_fields"
        )
        query = OnlyFields(
            PlainText("quid"),
            fields=["foo"],
            only_model=ContentPage,
        )
        compiler = OnlyFieldSearchQueryCompiler(ContentPage.objects.all(), query)
        compiler._compile_query(query, Field("bar"), 3.5)
        assert (
            call(["foo"], get_searchable_fields__kwargs={"only_model": ContentPage})
            in mock_remap.call_args_list
        )

    def test_compile_query_onlyfields_logic(self, mocker):
        remapped_field = mocker.Mock(field_name="baz")
        mocker.patch(
            "extended_search.backends.backend.ExtendedSearchQueryCompiler._remap_fields",
            return_value=[remapped_field],
        )
        mock_parent = mocker.patch(
            "extended_search.backends.backend.ExtendedSearchQueryCompiler._compile_query"
        )
        mock_join_and_compile = mocker.patch(
            "extended_search.backends.backend.ExtendedSearchQueryCompiler._join_and_compile_queries"
        )
        subquery = PlainText("quid")
        query = OnlyFields(subquery, fields=["foo"], only_model=ContentPage)
        compiler = OnlyFieldSearchQueryCompiler(ContentPage.objects.all(), query)
        field = Field(compiler.mapping.all_field_name)
        compiler._compile_query(query, field, 8.3)
        mock_join_and_compile.assert_called_once_with(subquery, [remapped_field], 8.3)
        mock_parent.assert_not_called()

        mock_parent.reset_mock()
        mock_join_and_compile.reset_mock()
        field = Field("foo")
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
            query.subquery, field
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
            query.subquery, field
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
