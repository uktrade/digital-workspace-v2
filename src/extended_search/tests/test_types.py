from enum import Enum

import pytest

from extended_search.types import AnalysisType, SearchQueryType


class TestAnalysisType:
    def test_extends_enum(self):
        assert issubclass(AnalysisType, Enum)

    def test_contains_all_valid_options(self):
        assert AnalysisType("tokenized") == AnalysisType.TOKENIZED
        assert AnalysisType("filter") == AnalysisType.FILTER
        assert AnalysisType("explicit") == AnalysisType.EXPLICIT
        assert AnalysisType("keyword") == AnalysisType.KEYWORD
        assert AnalysisType("ngram") == AnalysisType.NGRAM
        with pytest.raises(ValueError, match="'ANYTHING' is not a valid AnalysisType"):
            AnalysisType("ANYTHING")
        assert [t.value for t in AnalysisType] == [
            "tokenized",
            "filter",
            "explicit",
            "keyword",
            "ngram",
        ]


class TestSearchQueryType:
    def test_extends_enum(self):
        assert issubclass(SearchQueryType, Enum)

    def test_contains_all_valid_options(self):
        assert SearchQueryType("phrase") == SearchQueryType.PHRASE
        assert SearchQueryType("query_and") == SearchQueryType.QUERY_AND
        assert SearchQueryType("query_or") == SearchQueryType.QUERY_OR
        assert SearchQueryType("fuzzy") == SearchQueryType.FUZZY
        with pytest.raises(
            ValueError, match="'ANYTHING' is not a valid SearchQueryType"
        ):
            SearchQueryType("ANYTHING")
        assert [t.value for t in SearchQueryType] == [
            "phrase",
            "query_and",
            "query_or",
            "fuzzy",
        ]
