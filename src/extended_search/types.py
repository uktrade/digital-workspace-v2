from enum import Enum


class SearchQueryType(Enum):
    PHRASE = "phrase"
    QUERY_AND = "query_and"
    QUERY_OR = "query_or"
    FUZZY = "fuzzy"


class AnalysisType(Enum):
    TOKENIZED = "tokenized"
    FILTER = "filter"
    EXPLICIT = "explicit"
    KEYWORD = "keyword"
    NGRAM = "ngram"
