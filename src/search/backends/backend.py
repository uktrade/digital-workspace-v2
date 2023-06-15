from wagtail.search.backends.elasticsearch7 import (
    Elasticsearch7SearchBackend,
    Elasticsearch7SearchQueryCompiler,
)
from wagtail.search.query import MATCH_NONE

from search.backends.query import Only


class CustomSearchQueryCompiler(Elasticsearch7SearchQueryCompiler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mapping = self.mapping_class(self.queryset.model)
        self.remapped_fields = self.remap_fields(self.fields)

    def remap_fields(self, fields):
        """
        Convert field names into index column names
        """
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
        if not isinstance(query, Only):
            return super()._compile_query(query, field, boost)

        if query.remapped_fields == []:
            query.remapped_fields = self.remap_fields(query.fields)

        if field in query.remapped_fields:
            return self._compile_query(query.subquery, field, boost)
        return self._compile_query(MATCH_NONE, field, boost)


class CustomSearchBackend(Elasticsearch7SearchBackend):
    query_compiler_class = CustomSearchQueryCompiler


SearchBackend = CustomSearchBackend
