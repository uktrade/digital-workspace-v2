from enum import Enum


class SearchQueryType(Enum):
    PHRASE = "PHRASE"
    QUERY_AND = "QUERY_AND"
    QUERY_OR = "QUERY_OR"
    FUZZY = "FUZZY"


class AnalysisType(Enum):
    TOKENIZED = "TOKENIZED"
    FILTER = "FILTER"
    EXPLICIT = "EXPLICIT"
    KEYWORD = "KEYWORD"
    PROXIMITY = "PROXIMITY"
