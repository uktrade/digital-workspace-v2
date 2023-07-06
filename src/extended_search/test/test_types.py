import pytest
from enum import Enum

from extended_search.types import SearchQueryType, AnalysisType


class TestAnalysisType:
    def test_extends_enum(self):
        assert issubclass(AnalysisType, Enum)

    def test_contains_all_valid_options(self):
        assert AnalysisType("TOKENIZED") == AnalysisType.TOKENIZED
        assert AnalysisType("FILTER") == AnalysisType.FILTER
        assert AnalysisType("EXPLICIT") == AnalysisType.EXPLICIT
        assert AnalysisType("KEYWORD") == AnalysisType.KEYWORD
        assert AnalysisType("PROXIMITY") == AnalysisType.PROXIMITY
        with pytest.raises(ValueError, match="'ANYTHING' is not a valid AnalysisType"):
            assert AnalysisType("ANYTHING") == AnalysisType.ANYTHING
        assert [t.value for t in AnalysisType] == [
            "TOKENIZED",
            "FILTER",
            "EXPLICIT",
            "KEYWORD",
            "PROXIMITY",
        ]


class TestSearchQueryType:
    def test_extends_enum(self):
        assert issubclass(SearchQueryType, Enum)

    def test_contains_all_valid_options(self):
        assert SearchQueryType("PHRASE") == SearchQueryType.PHRASE
        assert SearchQueryType("QUERY_AND") == SearchQueryType.QUERY_AND
        assert SearchQueryType("QUERY_OR") == SearchQueryType.QUERY_OR
        assert SearchQueryType("FUZZY") == SearchQueryType.FUZZY
        with pytest.raises(
            ValueError, match="'ANYTHING' is not a valid SearchQueryType"
        ):
            assert SearchQueryType("ANYTHING") == SearchQueryType.ANYTHING
        assert [t.value for t in SearchQueryType] == [
            "PHRASE",
            "QUERY_AND",
            "QUERY_OR",
            "FUZZY",
        ]
