import re
import unicodedata
from typing import Optional

from django.conf import settings
from wagtail.search.query import Fuzzy, Or, Phrase, PlainText

from extended_search.index import Indexed
from extended_search.query import OnlyFields
from extended_search.query_builder import CustomQueryBuilder
from extended_search import settings as search_settings


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


def get_query_info(fields, field, index_field, suffix_map):
    if field is None:
        return fields

    if isinstance(field, Or):
        for f in field.subqueries:
            fields = get_query_info(fields, f, index_field, suffix_map)

    elif isinstance(field, OnlyFields):
        core_field = field.subquery.subquery

        analyzer_name = "tokenizer"
        for analyzer, suffix in suffix_map:
            if suffix and suffix in field.fields[0]:
                analyzer_name = analyzer

        if isinstance(core_field, Phrase):
            query_type = "phrase"
        elif isinstance(core_field, Fuzzy):
            query_type = "fuzzy"
        elif isinstance(core_field, PlainText):
            if core_field.operator == "and":
                query_type = "query_and"
            else:
                query_type = "query_or"
        fields.append(
            {
                "query_type": query_type,
                "field": index_field.model_field_name,
                "analyzer": analyzer_name,
                "boost": field.subquery.boost,
            }
        )
    return fields


def get_query_info_for_model(model_class: Indexed, query: str) -> list:
    query_info: list = []
    analyzer_field_suffices = [
        (k, v["index_fieldname_suffix"])
        for k, v in search_settings.extended_search_settings["analyzers"].items()
    ]
    for index_field in model_class.indexed_fields:
        field = CustomQueryBuilder.swap_variables(
            CustomQueryBuilder._build_search_query(model_class, index_field),
            query,
        )
        get_query_info(query_info, field, index_field, analyzer_field_suffices)
    return query_info


def get_bad_score_threshold(query, category):
    """
    Gets the average of all the boosts related to the query so that a threshold
    is identified.
    """
    from search.templatetags.search import SEARCH_VECTORS

    model_class = SEARCH_VECTORS[category].model
    if not model_class:
        return 0

    model_query_info = get_query_info_for_model(model_class, query)

    boost_values = set()
    for field_query_info in model_query_info:
        boost_values.add(round(field_query_info["boost"], 2))

    avg_boost_value = sum(boost_values) / len(boost_values)

    return avg_boost_value * settings.BAD_SEARCH_SCORE_MULTIPLIERS.get(category, 1)


# Triggers the conditional rendering on the FE message if the search yields low score results
def has_only_bad_results(query, category, pinned_results, search_results):
    if pinned_results:
        return False
    if not search_results:
        return False
    bad_score_threshold = get_bad_score_threshold(query, category)
    highest_score = search_results[0]._score
    return highest_score <= bad_score_threshold
