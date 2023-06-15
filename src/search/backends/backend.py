from wagtail.search.backends.elasticsearch7 import (
    Elasticsearch7SearchBackend,
    Elasticsearch7SearchQueryCompiler,
)
from wagtail.search.query import MATCH_NONE

from search.backends.query import Only


class CustomSearchQueryCompiler(Elasticsearch7SearchQueryCompiler):
    def _compile_query(self, query, field, boost=1.0):
        if not isinstance(query, Only):
            return super()._compile_query(query, field, boost)

        if field in query.fields:
            return self._compile_query(query.subquery, field, boost)
        return self._compile_query(MATCH_NONE, field, boost)

    def get_inner_query(self):
        if self.remapped_fields:
            fields = self.remapped_fields
        elif self.partial_match:
            fields = [self.mapping.all_field_name, self.mapping.edgengrams_field_name]
        else:
            fields = [self.mapping.all_field_name]

        print("FIELDS")
        print(fields)

        return super().get_inner_query()


class CustomSearchBackend(Elasticsearch7SearchBackend):
    query_compiler_class = CustomSearchQueryCompiler


SearchBackend = CustomSearchBackend
