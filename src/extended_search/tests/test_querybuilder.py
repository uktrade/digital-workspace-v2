import pytest
from wagtail.search.query import Boost, Fuzzy, Phrase, PlainText

from content.models import ContentPage
from extended_search.backends.query import OnlyFields
from extended_search.managers import get_indexed_field_name, get_search_query
from extended_search.managers.index import ModelIndexManager
from extended_search.managers.query_builder import QueryBuilder
from extended_search.models import Setting
from extended_search.settings import extended_search_settings
from extended_search.types import AnalysisType, SearchQueryType


class TestManagerInit:
    @pytest.mark.django_db
    def test_get_indexed_field_name_uses_settings_correctly(self):
        with pytest.raises(AttributeError):
            get_indexed_field_name("foo", "bar")
        analyzer = AnalysisType.TOKENIZED
        assert get_indexed_field_name("foo", analyzer) == "foo"

        Setting.objects.create(
            key=f"analyzers__{analyzer.value}__index_fieldname_suffix", value="bar"
        )
        assert (
            extended_search_settings[
                f"analyzers__{analyzer.value}__index_fieldname_suffix"
            ]
            == "bar"
        )
        assert get_indexed_field_name("foo", analyzer) == "foobar"

    def test_get_search_query_from_mapping_uses_settings_and_submethods(self):
        ...

    def test_get_search_query_from_mapping_gets_right_number_of_subqueries(self):
        ...

    def test_get_search_query_from_mapping_handles_relatedfields(self):
        ...

    def test_get_search_query_from_mapping_handles_searchfield(self):
        ...

    def test_get_search_query_from_mapping_handles_fuzzy(self):
        ...

    def test_get_search_query_uses_mapping(self, mocker):
        mock_map = mocker.patch(
            "extended_search.managers.index.ModelIndexManager.get_mapping",
            return_value=[],
        )
        mock_q = mocker.patch(
            "extended_search.managers.query_builder.QueryBuilder._get_search_query_from_mapping",
            return_value=[],
        )
        assert get_search_query(ModelIndexManager, "query", ContentPage) == None
        mock_map.assert_called_once_with()

        mock_map.return_value = ["--one--"]
        assert get_search_query(ModelIndexManager, "query", ContentPage) == "--one--"
        mock_q.assert_called_once_with("query", ContentPage, "--one--")


class TestQueryBuilder:
    def test_get_inner_searchquery_for_querytype_doesnt_use_and_if_single_word(self):
        assert (
            QueryBuilder._get_inner_searchquery_for_querytype(
                "searchquery", SearchQueryType.QUERY_AND
            )
            is None
        )
        result = QueryBuilder._get_inner_searchquery_for_querytype(
            "search query", SearchQueryType.QUERY_AND
        )
        assert result is not None

    def test_get_inner_searchquery_for_querytype_handles_searchquerytypes(self):
        result = QueryBuilder._get_inner_searchquery_for_querytype(
            "search query", SearchQueryType.PHRASE
        )
        assert isinstance(result, Phrase)
        assert result.query_string == "search query"

        result = QueryBuilder._get_inner_searchquery_for_querytype(
            "search query", SearchQueryType.QUERY_AND
        )
        assert isinstance(result, PlainText)
        assert result.operator == "and"
        assert result.query_string == "search query"

        result = QueryBuilder._get_inner_searchquery_for_querytype(
            "search query", SearchQueryType.QUERY_OR
        )
        assert isinstance(result, PlainText)
        assert result.operator == "or"
        assert result.query_string == "search query"

        result = QueryBuilder._get_inner_searchquery_for_querytype(
            "search query", SearchQueryType.FUZZY
        )
        assert isinstance(result, Fuzzy)
        assert result.query_string == "search query"

        with pytest.raises(ValueError):
            QueryBuilder._get_inner_searchquery_for_querytype(
                "search query", "anything"  # type: ignore
            )

    @pytest.mark.django_db
    def test_get_boost_for_field_querytype_analysistype_handles_types(self):
        Setting.objects.create(
            key=f"boost_parts__fields__content.contentpage.title", value=555.55
        )
        query_boost = float(
            extended_search_settings["boost_parts"]["query_types"]["phrase"]
        )
        analyzer_boost = float(
            extended_search_settings["boost_parts"]["analyzers"]["explicit"]
        )
        field_boost = float(
            extended_search_settings["boost_parts"]["fields"][
                "content.contentpage.title"
            ]
        )
        # check we're using all 3 values multiplied together
        assert (query_boost * analyzer_boost * field_boost) != (
            query_boost * analyzer_boost
        )
        assert (query_boost * analyzer_boost * field_boost) != (
            query_boost * field_boost
        )
        assert (query_boost * analyzer_boost * field_boost) != (
            analyzer_boost * field_boost
        )
        assert (query_boost * analyzer_boost * field_boost) != (query_boost)
        assert (query_boost * analyzer_boost * field_boost) != (analyzer_boost)
        assert (query_boost * analyzer_boost * field_boost) != (field_boost)
        assert QueryBuilder._get_boost_for_field_querytype_analysistype(
            "title", ContentPage, SearchQueryType.PHRASE, AnalysisType.EXPLICIT, {}
        ) == (query_boost * analyzer_boost * field_boost)

        query_boost = float(
            extended_search_settings["boost_parts"]["query_types"]["query_and"]
        )
        assert QueryBuilder._get_boost_for_field_querytype_analysistype(
            "title", ContentPage, SearchQueryType.QUERY_AND, AnalysisType.EXPLICIT, {}
        ) == (query_boost * analyzer_boost * field_boost)

        query_boost = float(
            extended_search_settings["boost_parts"]["query_types"]["query_or"]
        )
        assert QueryBuilder._get_boost_for_field_querytype_analysistype(
            "title", ContentPage, SearchQueryType.QUERY_OR, AnalysisType.EXPLICIT, {}
        ) == (query_boost * analyzer_boost * field_boost)

        query_boost = float(
            extended_search_settings["boost_parts"]["query_types"]["fuzzy"]
        )
        assert QueryBuilder._get_boost_for_field_querytype_analysistype(
            "title", ContentPage, SearchQueryType.FUZZY, AnalysisType.EXPLICIT, {}
        ) == (query_boost * analyzer_boost * field_boost)

        analyzer_boost = float(
            extended_search_settings["boost_parts"]["analyzers"]["tokenized"]
        )
        assert QueryBuilder._get_boost_for_field_querytype_analysistype(
            "title", ContentPage, SearchQueryType.FUZZY, AnalysisType.TOKENIZED, {}
        ) == (query_boost * analyzer_boost * field_boost)

        analyzer_boost = float(
            extended_search_settings["boost_parts"]["analyzers"]["explicit"]
        )
        assert QueryBuilder._get_boost_for_field_querytype_analysistype(
            "title", ContentPage, SearchQueryType.FUZZY, AnalysisType.KEYWORD, {}
        ) == (query_boost * analyzer_boost * field_boost)

        with pytest.raises(ValueError):
            QueryBuilder._get_boost_for_field_querytype_analysistype(
                "title", ContentPage, "anything", AnalysisType.KEYWORD, {}
            )

        with pytest.raises(ValueError):
            QueryBuilder._get_boost_for_field_querytype_analysistype(
                "title", ContentPage, SearchQueryType.FUZZY, "anything", {}
            )

    def test_get_searchquery_for_etc_uses_submethods(self, mocker):
        mock_query = mocker.patch(
            "extended_search.managers.query_builder.QueryBuilder._get_inner_searchquery_for_querytype"
        )
        mock_boost = mocker.patch(
            "extended_search.managers.query_builder.QueryBuilder._get_boost_for_field_querytype_analysistype"
        )
        mock_name = mocker.patch(
            "extended_search.managers.query_builder.get_indexed_field_name"
        )
        mock_query.return_value = None
        result = QueryBuilder._get_searchquery_for_query_field_querytype_analysistype(
            "query",
            ContentPage,
            "title",
            SearchQueryType.PHRASE,
            AnalysisType.EXPLICIT,
            {},
        )
        assert result is None
        mock_query.assert_called_once_with("query", SearchQueryType.PHRASE)

        mock_query.return_value = Phrase("query")
        mock_boost.return_value = 333.33
        mock_name.return_value = "foo_bar_baz"
        result = QueryBuilder._get_searchquery_for_query_field_querytype_analysistype(
            "query",
            ContentPage,
            "title",
            SearchQueryType.PHRASE,
            AnalysisType.EXPLICIT,
            {},
        )
        assert isinstance(result, OnlyFields)
        assert result.fields == ["foo_bar_baz"]
        subquery = result.subquery
        assert isinstance(subquery, Boost)
        assert subquery.boost == 333.33
        subquery = subquery.subquery
        assert subquery == mock_query.return_value
        mock_query.assert_called_with("query", SearchQueryType.PHRASE)
        mock_boost.assert_called_with(
            "title", ContentPage, SearchQueryType.PHRASE, AnalysisType.EXPLICIT, {}
        )
        mock_name.assert_called_with("title", AnalysisType.EXPLICIT)

    def test_add_to_query(self):
        # using sets because the | operator is used to join querysets, and it's also vaslid to use on sets
        assert QueryBuilder._add_to_query(
            set(["a", "b"]),
            None,
        ) == set(["a", "b"])
        assert QueryBuilder._add_to_query(
            None,
            set(["a", "b"]),
        ) == set(["a", "b"])
        assert QueryBuilder._add_to_query(
            set(["a", "b"]),
            set(["c", "d"]),
        ) == set(["a", "b", "c", "d"])
