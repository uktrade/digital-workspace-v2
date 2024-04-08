from typing import Any, List, Union

from wagtail.search.backends.elasticsearch6 import Field
from wagtail.search.backends.elasticsearch7 import (
    Elasticsearch7Mapping,
    Elasticsearch7SearchBackend,
    Elasticsearch7SearchQueryCompiler,
)
from wagtail.search.index import SearchField
from wagtail.search.query import MATCH_NONE, Fuzzy, MatchAll, Not, Phrase, PlainText

from extended_search.query import Filtered, Nested, OnlyFields
from extended_search.index import RelatedFields


class FilteredSearchMapping(Elasticsearch7Mapping):
    def get_field_column_name(self, field):
        if isinstance(field, str) and field == "content_type":
            return "content_type"
        return super().get_field_column_name(field)


class ExtendedSearchQueryCompiler(Elasticsearch7SearchQueryCompiler):
    """
    Acting as a placeholder for upstream merges to Wagtail in a PR; this class
    doesn't change any behaviour but instead assigns responsibility for
    particular aspects to smaller methods to make it easier to override. In the
    PR maybe worth referencing https://github.com/wagtail/wagtail/issues/5422
    """

    def __init__(self, *args, **kwargs):
        """Remove this when we get wagtail PR 11018 merged & deployed"""
        super().__init__(*args, **kwargs)
        self.remapped_fields = self.remapped_fields or [
            Field(self.mapping.all_field_name)
        ]

    def get_boosted_fields(self, fields):
        """
        This is needed because we are backporting to strings WAY TOO EARLY
        """
        boostable_fields = [self.to_field(f) for f in fields]

        return super().get_boosted_fields(boostable_fields)

    def get_searchable_fields(self):
        return self.queryset.model.get_searchable_search_fields()

    def _remap_fields(self, fields):
        """
        Convert field names into index column names
        """
        if fields is None:
            return None

        remapped_fields = []
        searchable_fields = {f.field_name: f for f in self.get_searchable_fields()}
        for field_name in fields:
            if field_name in searchable_fields:
                field_name = self.mapping.get_field_column_name(
                    searchable_fields[field_name]
                )
            else:
                # @TODO this works but ideally we'd move get_field_column_name to handle this directly
                field_name_parts = field_name.split(".")
                if field_name_parts[0] in searchable_fields:
                    field_name = self.mapping.get_field_column_name(
                        searchable_fields[field_name_parts[0]]
                    )
                    field_name_remainder = ".".join(field_name_parts[1:])
                    field_name = f"{field_name}.{field_name_remainder}"

            remapped_fields.append(field_name)

        return [Field(field) for field in remapped_fields]

    def _join_and_compile_queries(self, query, fields, boost=1.0):
        """
        Handle a generalised situation of one or more queries that need
        compilation and potentially joining as siblings. If more than one field
        then compile a query for each field then combine with disjunction
        max (or operator which takes the max score out of each of the
        field queries)
        """
        if len(fields) == 1:
            return self._compile_query(query, fields[0], boost)
        else:
            field_queries = []
            for field in fields:
                field_queries.append(self._compile_query(query, field, boost))

            return {"dis_max": {"queries": field_queries}}

    def to_string(self, field: Union[str, Field]) -> str:
        if isinstance(field, Field):
            return field.field_name
        return field

    def to_field(self, field: Union[str, Field]) -> Field:
        if isinstance(field, Field):
            return field
        return Field(field)

    def backport_fields(self, fields: List[Any]) -> List[str]:
        """
        Convert a list of Field objects to a list of strings to be compatible
        with older versions of the code.
        """
        if not fields:
            return fields

        if not isinstance(fields[0], list):
            return [self.to_string(f) for f in fields]

        new_fields = []
        for field in fields:
            backported_fields = self.backport_fields(field)
            for backported_field in backported_fields:
                new_fields.append(backported_field)
        return new_fields

    def _compile_plaintext_query(self, query, fields, boost=1.0):
        return super()._compile_plaintext_query(
            query, self.backport_fields(fields), boost
        )

    def _compile_fuzzy_query(self, query, fields):
        return super()._compile_fuzzy_query(query, self.backport_fields(fields))

    def _compile_phrase_query(self, query, fields):
        return super()._compile_phrase_query(query, self.backport_fields(fields))

    def get_inner_query(self):
        """
        This is a brittle override of the Elasticsearch7SearchQueryCompiler.
        get_inner_query, acting as a stand in for getting these changes merged
        upstream. It exists in order to break out the _join_and_compile_queries
        method
        """
        fields = [self.to_field(f) for f in self.remapped_fields]

        if len(fields) == 0:
            # No fields. Return a query that'll match nothing
            return {"bool": {"mustNot": {"match_all": {}}}}

        # Handle MatchAll and PlainText separately as they were supported
        # before "search query classes" was implemented and we'd like to
        # keep the query the same as before
        if isinstance(self.query, MatchAll):
            return {"match_all": {}}

        elif isinstance(self.query, PlainText):
            return self._compile_plaintext_query(self.query, fields)

        elif isinstance(self.query, Phrase):
            return self._compile_phrase_query(self.query, fields)

        elif isinstance(self.query, Fuzzy):
            return self._compile_fuzzy_query(self.query, fields)

        elif isinstance(self.query, Not):
            return {
                "bool": {
                    "mustNot": [
                        self._compile_query(self.query.subquery, field)
                        for field in fields
                    ]
                }
            }

        else:
            return self._join_and_compile_queries(self.query, fields)


class OnlyFieldSearchQueryCompiler(ExtendedSearchQueryCompiler):
    """
    Acting as a placeholder for upstream merges to Wagtail in a separate PR to
    the ExtendedSearchQueryCompiler; this exists to support the new OnlyFields
    SearchQuery
    """

    def _compile_query(self, query, field, boost=1.0):
        """
        Override the parent method to handle specifics of the OnlyFields
        SearchQuery.
        """
        if not isinstance(query, OnlyFields):
            return super()._compile_query(query, field, boost)

        remapped_fields = self._remap_fields(query.fields)

        if isinstance(field, list) and len(field) == 1:
            field = field[0]

        if field.field_name == self.mapping.all_field_name:
            # We are using the "_all_text" field proxy (i.e. the search()
            # method was called without the fields kwarg), but now we want to
            # limit the downstream fields compiled to those explicitly defined
            # in the OnlyFields query
            return self._join_and_compile_queries(
                query.subquery, remapped_fields, boost
            )

        elif field.field_name in remapped_fields:
            # Fields were defined explicitly upstream, and we are dealing with
            # one that's in the OnlyFields filter
            return self._compile_query(query.subquery, field, boost)

        else:
            # Exclude this field from any further downstream compilation: it
            # was defined in the search() method but has been excluded from
            # this part of the tree with an OnlyFields filter
            return self._compile_query(MATCH_NONE, field, boost)


class NestedSearchQueryCompiler(ExtendedSearchQueryCompiler):
    def get_searchable_fields(self):
        return [
            f
            for f in self.queryset.model.get_search_fields()
            if isinstance(f, SearchField) or isinstance(f, RelatedFields)
        ]

    def _compile_query(self, query, field, boost=1.0):
        if isinstance(query, Nested):
            return self._compile_nested_query(query, [field], boost)
        return super()._compile_query(query, field, boost)

    def _compile_nested_query(self, query, fields, boost=1.0):
        """
        Add OS DSL elements to support Nested fields
        """
        return {
            "nested": {
                "path": query.path,
                "query": self._join_and_compile_queries(query.subquery, fields, boost),
            }
        }


class FilteredSearchQueryCompiler(ExtendedSearchQueryCompiler):
    def _compile_query(self, query, field, boost=1.0):
        if isinstance(query, Filtered):
            return self._compile_filtered_query(query, [field], boost)
        return super()._compile_query(query, field, boost)

    def _compile_filtered_query(self, query, fields, boost=1.0):
        """
        Add OS DSL elements to support Filtered fields
        """
        compiled_filters = [self._process_lookup(*f) for f in query.filters]
        if len(compiled_filters) == 1:
            compiled_filters = compiled_filters[0]

        return {
            "bool": {
                "must": self._join_and_compile_queries(query.subquery, fields, boost),
                "filter": compiled_filters,
            }
        }

    def _process_lookup(self, field, lookup, value):
        # @TODO not pretty given get_field_column_name is already overridden
        if isinstance(field, str):
            column_name = field
        else:
            column_name = self.mapping.get_field_column_name(field)

        if lookup == "contains":
            return {"match": {column_name: value}}

        if lookup == "excludes":
            return {"bool": {"mustNot": {"terms": {column_name: value}}}}

        return super()._process_lookup(field, lookup, value)


class BoostSearchQueryCompiler(ExtendedSearchQueryCompiler):
    def _compile_query(self, query, field, boost=1.0):
        if isinstance(query, Fuzzy):
            return self._compile_fuzzy_query(query, [field], boost)
        if isinstance(query, Phrase):
            return self._compile_phrase_query(query, [field], boost)
        return super()._compile_query(query, field, boost)

    def _compile_fuzzy_query(self, query, fields, boost=1.0):
        """
        Support boosting
        """
        match_query = super()._compile_fuzzy_query(query, fields)

        if boost != 1.0:
            if "multi_match" in match_query:
                match_query["multi_match"]["boost"] = boost
            else:
                for field in fields:
                    match_query["match"][field.field_name]["boost"] = boost

        return match_query

    def _compile_phrase_query(self, query, fields, boost=1.0):
        """
        Support boosting
        """
        match_query = super()._compile_phrase_query(query, fields)

        if boost != 1.0:
            if "multi_match" in match_query:
                match_query["multi_match"]["boost"] = boost
            else:
                for field in fields:
                    query = match_query["match_phrase"][field.field_name]
                    match_query["match_phrase"][field.field_name] = {
                        "query": query,
                        "boost": boost,
                    }

        return match_query


class CustomSearchMapping(
    FilteredSearchMapping,
): ...


class CustomSearchQueryCompiler(
    BoostSearchQueryCompiler,
    FilteredSearchQueryCompiler,
    NestedSearchQueryCompiler,
    OnlyFieldSearchQueryCompiler,
):
    mapping_class = CustomSearchMapping


class CustomSearchBackend(Elasticsearch7SearchBackend):
    query_compiler_class = CustomSearchQueryCompiler
    mapping_class = CustomSearchMapping


SearchBackend = CustomSearchBackend
