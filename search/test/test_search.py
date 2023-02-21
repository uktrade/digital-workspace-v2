import pytest

from search.search import sanitize_search_query


@pytest.mark.parametrize(
    "query,result",
    [
        ("Gôod morninç øæå", "Good morninc a"),
        (
            "Mieux vaut être seul que mal accompagné",
            "Mieux vaut etre seul que mal accompagne",
        ),
        ("Après la pluie, le beau temps", "Apres la pluie le beau temps"),
        ("À bon chat, bon rat", "A bon chat bon rat"),
        ("Lăpușneanu", "Lapusneanu"),
        ("Пожалуйста", ""),
        # ensure composite chars are also folded
        ("Ç is the same as \u0043\u0327", "C is the same as C"),
    ],
)
def test_sanitize_asciifolds_accented_chars(query, result):
    assert sanitize_search_query(query) == result


@pytest.mark.parametrize(
    "query,result",
    [
        (None, ""),
        ("¯\_(ツ)_/¯", " __ "),
        ("!/(^&*)\\+{[@]}", ""),
    ],
)
def test_sanitize_returns_str_containing_only_safe_chars(query, result):
    assert sanitize_search_query(query) == result


@pytest.mark.parametrize(
    "query,result",
    [
        ("query", "query"),
        ("a basic query", "a basic query"),
        ("a 'more complex' query", "a 'more complex' query"),
        (
            "a 'very complex' query with 'multiple phrases'",
            "a 'very complex' query with 'multiple phrases'",
        ),
        # only preserve single level deep
        (
            "a 'very complex' query with '\"multiple nested\" phrases'",
            "a 'very complex' query with 'multiple nested phrases'",
        ),
    ],
)
def test_sanitize_preserves_query_terms_and_phrases(query, result):
    assert sanitize_search_query(query) == result


@pytest.mark.parametrize(
    "query,result",
    [
        ("a 'phrased' query", "a 'phrased' query"),
        # quote styles are rationalised
        ('another "phrased" query', "another 'phrased' query"),
        ('a "misquoted query', "a misquoted query"),
        ("another misquoted' query", "another misquoted query"),
        # it will always match the first and second quotes of the same type
        ("a misquoted' query with 'a phrase'", "a misquoted' query with 'a phrase"),
        (
            "a misquoted 'query with' 'several' 'phrases",
            "a misquoted 'query with' 'several' phrases",
        ),
    ],
)
def test_sanitize_rationalises_valid_quotes(query, result):
    assert sanitize_search_query(query) == result
