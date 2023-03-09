import re
import unicodedata
from collections import deque
from typing import Optional

from wagtail.search.query import Phrase
from wagtail.search.utils import parse_query_string


def sanitize_search_query(query: Optional[str] = None) -> str:
    if query is None:
        return ""

    # find all properly quoted substrings with matching opening and closing "|'
    # re.split returns both matches and unmatched parts so we process everything
    matches = re.split(r"([\"'])(.*?)(\1)", query)

    output = ""
    quote_next_match = False
    valid_quotes = ['"', "'"]
    for match in matches:
        if match == "":
            continue
        if match in valid_quotes and not quote_next_match:
            quote_next_match = True  # opening quote found
            continue
        if match in valid_quotes and quote_next_match:
            quote_next_match = False  # closing quote found
            continue

        # ascii-fold all chars that can be folded
        match = unicodedata.normalize("NFKD", match)

        # replace all remaining url-unsafe chars
        cleaned_match = re.sub(r"[^a-zA-Z0-9-.~_\s]", "", match)
        if quote_next_match:
            cleaned_match = f"'{cleaned_match}'"

        output += cleaned_match

    return output


# FIXME: add tests
def get_query_parts_from_wagtail_query(query):
    filters, query = parse_query_string(query)

    stack = deque([query])

    while stack:
        query = stack.pop()

        if subqueries := getattr(query, "subqueries", None):
            stack.extendleft(subqueries)
        else:
            if isinstance(query, Phrase):
                yield query.query_string
            else:
                yield from query.query_string.split(" ")


def normalize_query(query: str) -> str:
    """_summary_

    Examples:
        >>> normalize_query("foo bar")
        'foo bar'
        >>> normalize_query(" foo bar ")
        'foo bar'

    Args:
        query (str): _description_

    Returns:
        str: _description_
    """

    query = query.strip()

    return query
