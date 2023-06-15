from wagtail.search.backends.elasticsearch7 import (
    Elasticsearch7SearchBackend,
    Elasticsearch7SearchQueryCompiler,
)
from wagtail.search.query import MATCH_NONE

from search.backends.query import Only


class CustomSearchQueryCompiler(Elasticsearch7SearchQueryCompiler):
    def __init__(self, *args, **kwargs):
        """
        Technically speaking this override doesn't do anything, it's more here
        as a reminder to modify the underlying class in this way than anything
        """
        super().__init__(*args, **kwargs)
        self.mapping = self.mapping_class(self.queryset.model)
        self.remapped_fields = self._remap_fields(self.fields)

    def _remap_fields(self, fields):
        """
        Convert field names into index column names
        """
        if fields is None:
            return None

        remapped_fields = []
        searchable_fields = {
            f.field_name: f
            for f in self.queryset.model.get_searchable_search_fields()
        }
        for field_name in fields:
            if field_name in searchable_fields:
                field_name = self.mapping.get_field_column_name(
                    searchable_fields[field_name]
                )

            remapped_fields.append(field_name)

        return remapped_fields

    def _compile_query(self, query, field, boost=1.0):
        """
        Override the parent method to handle specifics of the Only SearchQuery
        """
        if not isinstance(query, Only):
            return super()._compile_query(query, field, boost)

        if query.remapped_fields is None:
            query.remapped_fields = self._remap_fields(query.fields)

        if field in query.remapped_fields:
            return self._compile_query(query.subquery, field, boost)
        return self._compile_query(MATCH_NONE, field, boost)

    def _query_contains(self, query, search_query_type):
        """
        Search the whole query tree to see if it contains the specified type of SearchQuery
        """
        if isinstance(query, search_query_type):
            return True

        if query.subqueries is None or len(query.subqueries) == 0:
            return False

        return any(
            [
                self._query_contains(child_query, search_query_type)
                for child_query in query.subqueries
            ]
        )

    def get_inner_query(self):
        if (
            not self.remapped_fields and
            self._query_contains(self.query, Only)
        ):
            self.fields = [f.field_name for f in self.queryset.model.get_searchable_search_fields()]
            self.remapped_fields = self._remap_fields(self.fields)

        return super().get_inner_query()


class CustomSearchBackend(Elasticsearch7SearchBackend):
    query_compiler_class = CustomSearchQueryCompiler


SearchBackend = CustomSearchBackend
