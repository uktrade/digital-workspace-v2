from django.test import Client, TestCase

from search.search import sanitize_search_query

class TestSearchUtils(TestCase):
    def test_sanitize_asciifolds_accented_chars(self):
        query = "Gôod morninç øæå"
        result = sanitize_search_query(query)
        self.assertEqual(result, "Good morninc a")

        query = "Mieux vaut être seul que mal accompagné"
        result = sanitize_search_query(query)
        self.assertEqual(result, "Mieux vaut etre seul que mal accompagne")

        query = "Après la pluie, le beau temps"
        result = sanitize_search_query(query)
        self.assertEqual(result, "Apres la pluie le beau temps")

        query = "À bon chat, bon rat"
        result = sanitize_search_query(query)
        self.assertEqual(result, "A bon chat bon rat")

        query = "Lăpușneanu"
        result = sanitize_search_query(query)
        self.assertEqual(result, "Lapusneanu")

        query = "Пожалуйста"
        result = sanitize_search_query(query)
        self.assertEqual(result, "")

        # ensure composite chars are also folded
        query = "Ç \u0043\u0327"
        result = sanitize_search_query(query)
        self.assertEqual(result, "C C")


    def test_sanitize_returns_str_containing_only_safe_chars(self):
        query = None
        result = sanitize_search_query(query)
        self.assertEqual(result, "")

        query = "¯\_(ツ)_/¯"
        result = sanitize_search_query(query)
        self.assertEqual(result, " __ ")

        query = "!/(^&*)\\+{[@]}"
        result = sanitize_search_query(query)
        self.assertEqual(result, "")


    def test_sanitize_preserves_query_terms_and_phrases(self):
        query = "query"
        result = sanitize_search_query(query)
        self.assertEqual(result, query)

        query = "a basic query"
        result = sanitize_search_query(query)
        self.assertEqual(result, query)

        query = "a 'more complex' query"
        result = sanitize_search_query(query)
        self.assertEqual(result, query)

        query = "a 'very complex' query with 'multiple phrases'"
        result = sanitize_search_query(query)
        self.assertEqual(result, query)

        # only preserve single level deep
        query = "a 'very complex' query with '\"multiple nested\" phrases'"
        result = sanitize_search_query(query)
        self.assertEqual(result, "a 'very complex' query with 'multiple nested phrases'")


    def test_sanitize_rationalises_valid_quotes(self):
        query = "a 'phrased' query"
        result = sanitize_search_query(query)
        self.assertEqual(result, query)

        # quote styles are rationalised
        query = 'another "phrased" query'
        result = sanitize_search_query(query)
        self.assertEqual(result, "another 'phrased' query")

        query = 'a "misquoted query'
        result = sanitize_search_query(query)
        self.assertEqual(result, "a misquoted query")

        query = "another misquoted' query"
        result = sanitize_search_query(query)
        self.assertEqual(result, "another misquoted query")

        # it will always match the first and second quotes of the same type
        query = "a misquoted' query with 'a phrase'"
        result = sanitize_search_query(query)
        self.assertEqual(result, "a misquoted' query with 'a phrase")

        query = "a misquoted 'query with' 'several' 'phrases"
        result = sanitize_search_query(query)
        self.assertEqual(result, "a misquoted 'query with' 'several' phrases")
