from wagtail.search.query import SearchQuery, MATCH_NONE
from wagtail.search.backend.elasticsearch7 import Elasticsearch7SearchQueryCompiler, Elasticsearch7SearchBackend


class Only(SearchQuery):
    def __init__(self, subquery: SearchQuery, boost: float, fields: list[str]):
        self.subquery = subquery
        self.boost = boost
        self.fields = fields

    def __repr__(self):
        return "<Only {} >".format(repr(self.subquery))


class CustomSearchQueryCompiler(Elasticsearch7SearchQueryCompiler):
    def _compile_query(self, query, field, boost=1.0):
        if not isinstance(query, Only):
            return super()._compile_query(self, query, field, boost):

        if field in query.fields:
            return self._compile_query(query.subquery, field, boost)
        return self._compile_query(MATCH_NONE, field, boost)


class CustomSearchBackend(Elasticsearch7SearchBackend):
    query_compiler_class = CustomSearchQueryCompiler


SearchBackend = CustomSearchBackend
