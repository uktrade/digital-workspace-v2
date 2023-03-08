import re
import unicodedata
from collections import deque
from typing import Optional


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


def normalize_query(query: str) -> str:
    """Return a normalized query string.

    Notes:
        - remove leading and trailing whitespace
        - collapse multiple spaces down to a single space

    Examples:
        >>> normalize_query(' foo  "bar baz"')
        'foo "bar baz"'

    Args:
        query: The query string, usually from a search input.

    Returns:
        A normalized query string.
    """
    query = query.strip()
    query = re.sub(r"\s+", " ", query)

    return query


RE_KEYWORDS_AND_PHRASES = re.compile(
    r"""
        # match a quoted phrase
        # balanced double quotes
        (?<!\\)\"  # unescaped double quote
        (.*?)  # any character lazy (group)
        (?<!\\)\"  # unescaped double quote
        # balanced single quotes (similar to balanced double quotes)
        | (?<!\\)\'(.*?)(?<!\\)\'  # (group)
        # unbalanced quote (captures to the end of the string)
        | [\"\'](.*)  # (group)
        # match an unquoted keyword
        | (\S+)  # capture non-whitespace characters (group)
    """,
    re.VERBOSE,
)


def split_query(query: str) -> list[str]:
    """Split the query into a list of keyword and phrases.

    Examples:
        One word:
        >>> split_query('hello')
        ['hello']

        Two words:
        >>> split_query('hello world')
        ['hello', 'world']

        Double quoted phrase:
        >>> split_query('hello "big world"')
        ['hello', 'big world']

        Single quoted phrase:
        >>> split_query('hello \\'big world\\'')
        ['hello', 'big world']

        Quotes in quotes:
        >>> split_query('hello "big \\'big world\\'"')
        ['hello', "big 'big world'"]

        Unbalanced quotes:
        >>> split_query('hello "big world')
        ['hello', 'big world']

        Escaped quotes:
        >>> split_query(r"hello 'john\\'s world'")
        ['hello', "john's world"]

        Empty query:
        >>> split_query("")
        []

    Args:
        query: The query string, usually from a search input.

    Returns:
        A list of keywords and phrases from the query.
    """
    if not query:
        return []

    query = normalize_query(query)

    parts = []

    for match in re.finditer(RE_KEYWORDS_AND_PHRASES, query):
        # grab the first group as only one should match
        group = [g for g in match.groups() if g][0]
        # unescape the escaped quotes
        group = re.sub(r"\\(\"|\')", lambda match: match.group(1), group)

        parts.append(group)

    return parts
