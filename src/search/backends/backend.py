from wagtail.search.backend.elasticsearch7 import (
    Elasticsearch7SearchBackend,
    Elasticsearch7SearchQueryCompiler,
)
from wagtail.search.query import MATCH_NONE

from src.search.backends.query import Only


class CustomSearchQueryCompiler(Elasticsearch7SearchQueryCompiler):
    def _compile_query(self, query, field, boost=1.0):
        if not isinstance(query, Only):
            return super()._compile_query(self, query, field, boost)

        if field in query.fields:
            return self._compile_query(query.subquery, field, boost)
        return self._compile_query(MATCH_NONE, field, boost)


class CustomSearchBackend(Elasticsearch7SearchBackend):
    query_compiler_class = CustomSearchQueryCompiler


SearchBackend = CustomSearchBackend
