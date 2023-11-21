from unittest.mock import call

import pytest

from content.models import ContentPage

from extended_search.settings import extended_search_settings
from extended_search.types import AnalysisType, SearchQueryType
from extended_search.query import Filtered, OnlyFields, Nested
from extended_search.query_builder import QueryBuilder, CustomQueryBuilder
from extended_search.index import SearchField, IndexedField, RelatedFields
from wagtail.search.query import Boost, Fuzzy, Or, Phrase, PlainText, SearchQuery


class MockModelClass:
    indexed_fields = []

    @classmethod
    def get_indexed_fields(cls):
        return cls.indexed_fields


class TestCustomQueryBuilder:
    query_builder_class = CustomQueryBuilder

    def test_build_query_for_model(self, mocker):
        mock_combine = mocker.patch(
            "extended_search.query_builder.CustomQueryBuilder._combine_queries",
            return_value="foo",
        )
        mock_build_search_query = mocker.patch(
            "extended_search.query_builder.CustomQueryBuilder._build_search_query",
            return_value=None,
        )
        assert CustomQueryBuilder.build_query_for_model(MockModelClass) is None
        mock_build_search_query.assert_not_called()
        mock_combine.assert_not_called()
        mock_build_search_query.reset_mock()
        mock_combine.reset_mock()

        MockModelClass.indexed_fields = ["--field--"]
        assert CustomQueryBuilder.build_query_for_model(MockModelClass) is None
        mock_build_search_query.assert_called_once_with(MockModelClass, "--field--")
        mock_combine.assert_not_called()
        mock_build_search_query.reset_mock()
        mock_combine.reset_mock()

        mock_build_search_query.return_value = "--query--"
        assert CustomQueryBuilder.build_query_for_model(MockModelClass) == "foo"
        mock_combine.assert_called_once_with(None, "--query--")

    def test_get_extended_models_with_unique_indexed_fields(self, mocker):
        base_model_class = mocker.Mock()
        extended_model_class = mocker.Mock()
        extended_model_class.__name__ = "extendedModel"
        extended_model_class._meta.app_label = "mock.extended"
        extended_model_class.has_indexmanager_direct_inner_class.return_value = False
        mock_get_models = mocker.patch(
            "extended_search.query_builder.get_indexed_models",
            return_value=[base_model_class],
        )
        mock_mro = mocker.patch(
            "extended_search.query_builder.inspect.getmro",
            return_value=[extended_model_class],
        )
        assert (
            CustomQueryBuilder.get_extended_models_with_unique_indexed_fields(
                base_model_class
            )
            == []
        )

        mock_get_models.return_value = [
            base_model_class,
            extended_model_class,
        ]
        assert (
            CustomQueryBuilder.get_extended_models_with_unique_indexed_fields(
                base_model_class
            )
            == []
        )

        extended_model_class.has_indexmanager_direct_inner_class.return_value = True
        assert (
            CustomQueryBuilder.get_extended_models_with_unique_indexed_fields(
                base_model_class
            )
            == []
        )

        mock_mro.return_value = [extended_model_class, base_model_class]
        assert CustomQueryBuilder.get_extended_models_with_unique_indexed_fields(
            base_model_class
        ) == [extended_model_class]

    def test_get_search_query(self, mocker):
        model_class = mocker.Mock()
        query = "foo"  # PlainText("foo")
        built_query = PlainText("foo")
        mock_build_search_query = mocker.patch(
            "extended_search.query_builder.CustomQueryBuilder.build_search_query",
            return_value=built_query,
        )
        output_query = PlainText("bar")
        mock_swap_variables = mocker.patch(
            "extended_search.query_builder.CustomQueryBuilder.swap_variables",
            return_value=output_query,
        )
        result = CustomQueryBuilder.get_search_query(model_class, query)
        mock_build_search_query.assert_called_once_with(model_class)
        mock_swap_variables.assert_called_once_with(built_query, query)
        assert result == output_query

    def test_swap_variables(self, mocker):
        query_str = "foo"
        query = Variable("search_query", SearchQueryType.PHRASE)
        result = CustomQueryBuilder.swap_variables(query, query_str)
        assert repr(result) == repr(Phrase("foo"))

        query = Or(
            [
                Variable("search_query", SearchQueryType.PHRASE),
                Variable("search_query", SearchQueryType.FUZZY),
            ]
        )
        result = CustomQueryBuilder.swap_variables(query, query_str)
        assert repr(result) == repr(
            Or(
                [
                    Phrase("foo"),
                    Fuzzy("foo"),
                ]
            )
        )

        query = And(
            [
                Variable("search_query", SearchQueryType.PHRASE),
                Variable("search_query", SearchQueryType.FUZZY),
            ]
        )
        result = CustomQueryBuilder.swap_variables(query, query_str)
        assert repr(result) == repr(
            And(
                [
                    Phrase("foo"),
                    Fuzzy("foo"),
                ]
            )
        )

        query = Not(Variable("search_query", SearchQueryType.PHRASE))
        result = CustomQueryBuilder.swap_variables(query, query_str)
        assert repr(result) == repr(Not(Phrase("foo")))

    @pytest.mark.xfail
    def test_build_search_query(self, mocker):
        model_class = mocker.Mock()
        extended_model_class = mocker.Mock()
        extended_model_class._meta.app_label = "mock"
        extended_model_class.__name__ = "extended_model"
        query = "foo"  # PlainText("foo")
        mock_get_extended_models = mocker.patch(
            "extended_search.query_builder.CustomQueryBuilder.get_extended_models_with_unique_indexed_fields",
            return_value=[extended_model_class],
        )
        mock_get_query = mocker.patch(
            "extended_search.query_builder.CustomQueryBuilder.build_query_for_model",
            return_value=PlainText("foo"),
        )
        result = CustomQueryBuilder.build_search_query(model_class)
        mock_get_extended_models.assert_called_once_with(model_class)
        mock_get_query.assert_has_calls(
            [
                call(extended_model_class, query),
                call(model_class, query),
            ]
        )
        assert repr(result) == repr(
            Or(
                [
                    Filtered(
                        subquery=PlainText("foo"),
                        filters=[
                            ("content_type", "excludes", ["mock.extended_model"]),
                        ],
                    ),
                    Filtered(
                        subquery=PlainText("foo"),
                        filters=[
                            ("content_type", "contains", "mock.extended_model"),
                        ],
                    ),
                ]
            )
        )


class TestQueryBuilder:
    query_builder_class = QueryBuilder

    def test_get_boost_for_field_querytype_analysistype(self, mocker):
        mock_boost_qt = mocker.patch(
            "extended_search.query_builder.QueryBuilder._get_boost_for_querytype",
            return_value=25,
        )
        mock_boost_at = mocker.patch(
            "extended_search.query_builder.QueryBuilder._get_boost_for_analysistype",
            return_value=125,
        )
        mock_boost_f = mocker.patch(
            "extended_search.query_builder.QueryBuilder._get_boost_for_field",
            return_value=33.3,
        )
        field = mocker.Mock()
        model = mocker.Mock()
        assert self.query_builder_class._get_boost_for_field_querytype_analysistype(
            model, SearchQueryType.FUZZY, AnalysisType.EXPLICIT, field
        ) == (
            mock_boost_qt.return_value
            * mock_boost_at.return_value
            * mock_boost_f.return_value
        )
        mock_boost_qt.assert_called_once_with(SearchQueryType.FUZZY)
        mock_boost_at.assert_called_once_with(AnalysisType.EXPLICIT)
        mock_boost_f.assert_called_once_with(model, field)

    def test_get_boost_for_field(self, mocker):
        mock_get_key = mocker.patch(
            "extended_search.query_builder.get_settings_field_key",
            return_value="--settings-key--",
        )
        field = mocker.Mock()
        model = mocker.Mock()
        assert self.query_builder_class._get_boost_for_field(model, field) == 1.0
        field.get_definition_model.assert_called_once_with(model)
        mock_get_key.assert_called_once_with(
            field.get_definition_model.return_value, field
        )

        extended_search_settings["boost_parts"]["fields"]["--settings-key--"] = 333.33
        assert self.query_builder_class._get_boost_for_field(model, field) == 333.33

    def test_get_boost_for_analysistype(self):
        with pytest.raises(ValueError):
            self.query_builder_class._get_boost_for_analysistype("foo")

        extended_search_settings["boost_parts"]["analyzers"]["explicit"] = 888.88
        assert (
            self.query_builder_class._get_boost_for_analysistype(AnalysisType.EXPLICIT)
            == 888.88
        )
        assert (
            self.query_builder_class._get_boost_for_analysistype(AnalysisType.TOKENIZED)
            == extended_search_settings["boost_parts"]["analyzers"]["tokenized"]
        )
        assert (
            self.query_builder_class._get_boost_for_analysistype(AnalysisType.KEYWORD)
            == extended_search_settings["boost_parts"]["analyzers"]["explicit"]
        )
        extended_search_settings["boost_parts"]["analyzers"]["explicit"] = None
        assert (
            self.query_builder_class._get_boost_for_analysistype(AnalysisType.EXPLICIT)
            == 1.0
        )

    def test_get_boost_for_querytype(self):
        with pytest.raises(ValueError):
            self.query_builder_class._get_boost_for_querytype("foo")

        extended_search_settings["boost_parts"]["query_types"]["phrase"] = 888.88
        assert (
            self.query_builder_class._get_boost_for_querytype(SearchQueryType.PHRASE)
            == 888.88
        )
        assert (
            self.query_builder_class._get_boost_for_querytype(SearchQueryType.QUERY_AND)
            == extended_search_settings["boost_parts"]["query_types"]["query_and"]
        )
        assert (
            self.query_builder_class._get_boost_for_querytype(SearchQueryType.QUERY_OR)
            == extended_search_settings["boost_parts"]["query_types"]["query_or"]
        )
        assert (
            self.query_builder_class._get_boost_for_querytype(SearchQueryType.FUZZY)
            == extended_search_settings["boost_parts"]["query_types"]["fuzzy"]
        )
        extended_search_settings["boost_parts"]["query_types"]["phrase"] = None
        assert (
            self.query_builder_class._get_boost_for_querytype(SearchQueryType.PHRASE)
            == 1.0
        )

    def test_get_inner_searchquery_for_querytype_doesnt_use_and_if_single_word(self):
        assert (
            self.query_builder_class._get_inner_searchquery_for_querytype(
                "searchquery", SearchQueryType.QUERY_AND
            )
            is None
        )
        result = self.query_builder_class._get_inner_searchquery_for_querytype(
            "search query", SearchQueryType.QUERY_AND
        )
        assert result is not None

    def test_get_inner_searchquery_for_querytype_handles_searchquerytypes(self):
        result = self.query_builder_class._get_inner_searchquery_for_querytype(
            "search query", SearchQueryType.PHRASE
        )
        assert isinstance(result, Phrase)
        assert result.query_string == "search query"

        result = self.query_builder_class._get_inner_searchquery_for_querytype(
            "search query", SearchQueryType.QUERY_AND
        )
        assert isinstance(result, PlainText)
        assert result.operator == "and"
        assert result.query_string == "search query"

        result = self.query_builder_class._get_inner_searchquery_for_querytype(
            "search query", SearchQueryType.QUERY_OR
        )
        assert isinstance(result, PlainText)
        assert result.operator == "or"
        assert result.query_string == "search query"

        result = self.query_builder_class._get_inner_searchquery_for_querytype(
            "search query", SearchQueryType.FUZZY
        )
        assert isinstance(result, Fuzzy)
        assert result.query_string == "search query"

        with pytest.raises(ValueError):
            self.query_builder_class._get_inner_searchquery_for_querytype(
                "search query", "anything"  # type: ignore
            )

    def test__get_search_query(self, mocker):
        model = mocker.Mock()
        indexed_field = mocker.Mock(spec=IndexedField)
        indexed_field.model_field_name = "indexed"
        related_fields = mocker.Mock(spec=RelatedFields)
        related_fields.model_field_name = "related"
        search_field = mocker.Mock(spec=SearchField)
        search_field.model_field_name = "search"
        query = PlainText("bar")
        mock_get_query_indexfield = mocker.patch(
            "extended_search.query_builder.QueryBuilder._get_search_query_for_indexfield",
            return_value="index-query",
        )
        mock_get_query_searchfield = mocker.patch(
            "extended_search.query_builder.QueryBuilder._get_search_query_for_searchfield",
            return_value="search-query",
        )
        mock_combine_queries = mocker.patch(
            "extended_search.query_builder.QueryBuilder._combine_queries",
            return_value=query,
        )
        mock_infer_analyzer = mocker.patch(
            "extended_search.query_builder.QueryBuilder.infer_analyzer_from_field"
        )

        assert (
            self.query_builder_class._get_search_query("foo", model, indexed_field)
            == "index-query"
        )
        mock_get_query_indexfield.assert_called_once_with(
            indexed_field, "foo", model, None
        )
        mock_get_query_searchfield.assert_not_called()
        mock_combine_queries.assert_not_called()
        mock_infer_analyzer.assert_not_called()

        mock_get_query_indexfield.reset_mock()
        assert (
            self.query_builder_class._get_search_query("foo", model, search_field)
            == "search-query"
        )
        mock_get_query_indexfield.assert_not_called()
        mock_get_query_searchfield.assert_called_once_with(
            search_field, "foo", model, None, mock_infer_analyzer.return_value
        )
        mock_combine_queries.assert_not_called()
        mock_infer_analyzer.assert_called_once_with(search_field)

        mock_get_query_searchfield.reset_mock()
        mock_infer_analyzer.reset_mock()
        related_fields.fields = [indexed_field, search_field]
        assert (
            self.query_builder_class._get_search_query("foo", model, related_fields)
            == query
        )
        mock_get_query_indexfield.assert_called_once()
        mock_get_query_searchfield.assert_called_once()
        count = 0
        for called, _ in mock_combine_queries.call_args_list:
            if len(called) > 0:
                if called[0] is None:
                    assert called[1] == "index-query"
                    count += 1
                elif called[0] == query:
                    assert called[1] == "search-query"
                    count += 1
                else:
                    assert isinstance(called[0], Nested)
                    assert called[0].subquery == query
                    assert called[0].path == "related"
                    assert called[1] is None
                    count += 1
        assert count == 3
        mock_infer_analyzer.assert_called_once()

    def test_infer_analyzer_from_field(self, mocker):
        field = mocker.Mock(spec=SearchField)
        field.kwargs = {}
        assert (
            self.query_builder_class.infer_analyzer_from_field(field)
            == AnalysisType.TOKENIZED
        )
        field.kwargs = {"es_extra": {}}
        assert (
            self.query_builder_class.infer_analyzer_from_field(field)
            == AnalysisType.TOKENIZED
        )

        analyzer_settings = extended_search_settings["analyzers"]
        for name, analyzer in analyzer_settings.items():
            field.kwargs = {"es_extra": {"es_analyzer": analyzer["es_analyzer"]}}
            assert self.query_builder_class.infer_analyzer_from_field(
                field
            ) == AnalysisType(name)

    def test_get_search_query_for_indexfield(self, mocker):
        mock_combine_queries = mocker.patch(
            "extended_search.query_builder.QueryBuilder._combine_queries",
        )
        mock_get_for_searchfield = mocker.patch(
            "extended_search.query_builder.QueryBuilder._get_search_query_for_searchfield",
            return_value="search-query",
        )
        mock_get_searchquery = mocker.patch(
            "extended_search.query_builder.QueryBuilder._get_searchquery_for_query_field_querytype_analysistype"
        )
        model = mocker.Mock()
        field = mocker.Mock()
        field.model_field_name = "model-field-name"
        field.search = False
        field.fuzzy = False
        field.get_search_analyzers.return_value = ["--analyzer-1--"]

        assert (
            self.query_builder_class._get_search_query_for_indexfield(
                field, "foo", model, "bar"
            )
            == "bar"
        )

        field.search = True
        assert (
            self.query_builder_class._get_search_query_for_indexfield(
                field, "foo", model, "bar"
            )
            == mock_combine_queries.return_value
        )
        mock_get_for_searchfield.assert_called_once_with(
            field, "foo", model, "bar", "--analyzer-1--"
        )
        mock_combine_queries.assert_called_once_with(
            mock_get_for_searchfield.return_value, "bar"
        )

        mock_get_for_searchfield.reset_mock()
        mock_combine_queries.reset_mock()
        field.get_search_analyzers.return_value = ["--analyzer-1--", "--analyzer-2--"]
        assert (
            self.query_builder_class._get_search_query_for_indexfield(
                field, "foo", model, "bar"
            )
            == mock_combine_queries.return_value
        )
        assert len(mock_get_for_searchfield.call_args_list) == 2
        mock_get_for_searchfield.assert_any_call(
            field, "foo", model, "bar", "--analyzer-1--"
        )
        mock_get_for_searchfield.assert_any_call(
            field, "foo", model, "bar", "--analyzer-2--"
        )
        assert len(mock_combine_queries.call_args_list) == 2

        mock_get_for_searchfield.reset_mock()
        mock_combine_queries.reset_mock()
        field.get_search_analyzers.return_value = ["--analyzer-1--"]
        field.fuzzy = True
        assert (
            self.query_builder_class._get_search_query_for_indexfield(
                field, "foo", model, "bar"
            )
            == mock_combine_queries.return_value
        )
        assert len(mock_get_for_searchfield.call_args_list) == 1
        mock_get_for_searchfield.assert_any_call(
            field, "foo", model, "bar", "--analyzer-1--"
        )
        assert len(mock_combine_queries.call_args_list) == 2
        mock_combine_queries.assert_any_call(
            mock_get_for_searchfield.return_value, "bar"
        )
        mock_combine_queries.assert_any_call(
            mock_get_searchquery.return_value, mock_combine_queries.return_value
        )
        mock_get_searchquery.assert_called_once_with(
            "foo",
            model,
            "model-field-name",
            SearchQueryType("fuzzy"),
            AnalysisType.TOKENIZED,
            field,
        )

    def test_get_search_query_for_searchfield(self):
        raise AssertionError()

    def test_get_searchquery_for_query_field_querytype_analysistype(self):
        raise AssertionError()

    def test_get_filter_field_variants(self):
        raise AssertionError()

    def test_combine_queries(self):
        # using sets because the | operator is used to join querysets, and it's also vaslid to use on sets
        assert self.query_builder_class._combine_queries(
            set(["a", "b"]),
            None,
        ) == set(["a", "b"])
        assert self.query_builder_class._combine_queries(
            None,
            set(["a", "b"]),
        ) == set(["a", "b"])
        assert self.query_builder_class._combine_queries(
            set(["a", "b"]),
            set(["c", "d"]),
        ) == set(["a", "b", "c", "d"])

    def test_get_searchquery_for_etc_uses_submethods(self, mocker):
        mock_query = mocker.patch(
            "extended_search.query_builder.QueryBuilder._get_inner_searchquery_for_querytype"
        )
        mock_boost = mocker.patch(
            "extended_search.query_builder.QueryBuilder._get_boost_for_field_querytype_analysistype"
        )
        mocker.patch(
            "extended_search.query_builder.get_indexed_field_name",
            return_value="foobar",
        )
        mock_query.return_value = None
        field = mocker.Mock()
        result = self.query_builder_class._get_searchquery_for_query_field_querytype_analysistype(
            "query",
            ContentPage,
            "title",
            SearchQueryType.PHRASE,
            AnalysisType.EXPLICIT,
            field,
        )
        assert result is None
        mock_query.assert_called_once_with("query", SearchQueryType.PHRASE)

        mock_query.return_value = Phrase("query")
        mock_boost.return_value = 333.33
        result = self.query_builder_class._get_searchquery_for_query_field_querytype_analysistype(
            "query",
            ContentPage,
            "title",
            SearchQueryType.PHRASE,
            AnalysisType.EXPLICIT,
            field,
        )
        assert isinstance(result, OnlyFields)
        assert result.fields == ["foobar"]
        subquery = result.subquery
        assert isinstance(subquery, Boost)
        assert subquery.boost == 333.33
        subquery = subquery.subquery
        assert subquery == mock_query.return_value
        mock_query.assert_called_with("query", SearchQueryType.PHRASE)
        mock_boost.assert_called_with(
            ContentPage, SearchQueryType.PHRASE, AnalysisType.EXPLICIT, field
        )
