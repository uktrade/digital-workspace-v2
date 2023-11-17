from typing import Optional

from wagtail.search.query import And, Fuzzy, Not, Or, Phrase, PlainText, SearchQuery

from extended_search.types import SearchQueryType


class Variable:
    def __init__(self, name: str, query_type: SearchQueryType) -> None:
        self.name = name
        self.query_type = query_type

    def output(self, query_str: str):
        # split can be super basic since we don't support advanced search
        query_parts = query_str.split()
        match self.query_type:
            case SearchQueryType.PHRASE:
                query = Phrase(query_str)
            case SearchQueryType.QUERY_AND:
                # check the query_str merits an AND - does it contain multiple words?
                if len(query_parts) > 1:
                    query = PlainText(query_str, operator="and")
                else:
                    query = None
            case SearchQueryType.QUERY_OR:
                query = PlainText(query_str, operator="or")
            case SearchQueryType.FUZZY:
                query = Fuzzy(query_str)
            case _:
                raise ValueError(f"{self.query_type} must be a valid SearchQueryType")
        return query


def swap_variables(query: SearchQuery, search_query: str) -> Optional[SearchQuery]:
    """
    Iterate through the query and swap out variables for the search_query.
    """

    if isinstance(query, Variable):
        return query.output(search_query)

    if hasattr(query, "subqueries"):
        query.subqueries = [swap_variables(sq, search_query) for sq in query.subqueries]
        query.subqueries = [sq for sq in query.subqueries if sq]

        if not query.subqueries:
            return None
        elif len(query.subqueries) == 1:
            return query.subqueries[0]

    if hasattr(query, "subquery"):
        query.subquery = swap_variables(query.subquery, search_query)
        if not query.subquery:
            return None

    return query
