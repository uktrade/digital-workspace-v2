from typing import Optional, Union

from wagtail.search.backends.elasticsearch7 import (
    Elasticsearch7Mapping,
    Elasticsearch7SearchBackend,
    Elasticsearch7SearchQueryCompiler,
    ElasticsearchAtomicIndexRebuilder,
    Field,
)
from wagtail.search.index import SearchField
from wagtail.search.query import MATCH_NONE, Fuzzy, MatchAll, Not, Phrase, PlainText

from extended_search import settings as search_settings
from extended_search.index import RelatedFields
from extended_search.query import Filtered, FunctionScore, Nested, OnlyFields
from extended_search.query_builder import build_queries_for_index


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

    def _remap_fields(
        self,
        fields,
        get_searchable_fields__args: Optional[tuple] = None,
        get_searchable_fields__kwargs: Optional[dict] = None,
    ):
        """
        Convert field names into index column names
        """
        if get_searchable_fields__args is None:
            get_searchable_fields__args = ()
        if get_searchable_fields__kwargs is None:
            get_searchable_fields__kwargs = {}

        if not fields:
            return super()._remap_fields(fields)

        remapped_fields = []

        searchable_fields = {
            f.field_name: f
            for f in self.get_searchable_fields(
                *get_searchable_fields__args,
                **get_searchable_fields__kwargs,
            )
        }

        for field_name in fields:
            field = searchable_fields.get(field_name)
            if field:
                field_name = self.mapping.get_field_column_name(field)
                remapped_fields.append(Field(field_name, field.boost or 1))
            else:
                # @TODO this works but ideally we'd move get_field_column_name to handle this directly
                field_name_parts = field_name.split(".")
                if field_name_parts[0] in searchable_fields:
                    parent_related_field = searchable_fields[field_name_parts[0]]
                    field_name = self.mapping.get_field_column_name(
                        parent_related_field
                    )
                    field_name_remainder = ".".join(field_name_parts[1:])
                    field_name = f"{field_name}.{field_name_remainder}"

                    # Get the field boost from the settings so it can be managed in the DB.
                    child_field = parent_related_field.get_related_field(
                        field_name_remainder
                    )
                    field_settings_key = search_settings.get_settings_field_key(
                        self.queryset.model, child_field
                    )
                    field_boost = float(
                        search_settings.extended_search_settings["boost_parts"][
                            "fields"
                        ].get(field_settings_key, 1)
                    )
                    remapped_fields.append(Field(field_name, boost=field_boost))

        return remapped_fields

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

    def _compile_plaintext_query(self, query, fields, boost=1.0):
        return super()._compile_plaintext_query(query, fields, boost)

    def _compile_fuzzy_query(self, query, fields):
        return super()._compile_fuzzy_query(query, fields)

    def _compile_phrase_query(self, query, fields):
        return super()._compile_phrase_query(query, fields)

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

    def get_searchable_fields(self, *args, only_model, **kwargs):
        if not only_model:
            return super().get_searchable_fields()
        return [
            f
            for f in only_model.get_search_fields(ignore_cache=True)
            if isinstance(f, SearchField) or isinstance(f, RelatedFields)
        ]

    def _compile_query(self, query, field, boost=1.0):
        """
        Override the parent method to handle specifics of the OnlyFields
        SearchQuery.
        """
        if not isinstance(query, OnlyFields):
            return super()._compile_query(query, field, boost)

        remapped_fields = self._remap_fields(
            query.fields,
            get_searchable_fields__kwargs={
                "only_model": query.only_model,
            },
        )

        if isinstance(field, list) and len(field) == 1:
            field = field[0]

        if field.field_name == self.mapping.all_field_name and remapped_fields:
            # We are using the "_all_text" field proxy (i.e. the search()
            # method was called without the fields kwarg), but now we want to
            # limit the downstream fields compiled to those explicitly defined
            # in the OnlyFields query
            return self._join_and_compile_queries(
                query.subquery, remapped_fields, boost
            )

        elif field.field_name in query.fields:
            # Fields were defined explicitly upstream, and we are dealing with
            # one that's in the OnlyFields filter
            return self._compile_query(query.subquery, field, boost)

        else:
            # Exclude this field from any further downstream compilation: it
            # was defined in the search() method but has been excluded from
            # this part of the tree with an OnlyFields filter
            return self._compile_query(MATCH_NONE, field, boost)


class NestedSearchQueryCompiler(ExtendedSearchQueryCompiler):
    def get_searchable_fields(self, *args, **kwargs):
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
                match_query["multi_match"]["boost"] = boost * fields[0].boost
            elif "match" in match_query:
                for field in fields:
                    match_query["match"][field.field_name]["boost"] = (
                        boost * field.boost
                    )

        return match_query

    def _compile_phrase_query(self, query, fields, boost=1.0):
        """
        Support boosting
        """
        match_query = super()._compile_phrase_query(query, fields)

        if boost != 1.0:
            if "multi_match" in match_query:
                match_query["multi_match"]["boost"] = boost * fields[0].boost
            elif "match_phrase" in match_query:
                for field in fields:
                    query = match_query["match_phrase"][field.field_name]
                    if isinstance(query, dict) and "boost" in query:
                        match_query["match_phrase"][field.field_name]["boost"] = (
                            boost * field.boost
                        )
                    else:
                        match_query["match_phrase"][field.field_name] = {
                            "query": query,
                            "boost": boost * field.boost,
                        }

        return match_query


class FunctionScoreSearchQueryCompiler(ExtendedSearchQueryCompiler):
    def _compile_query(self, query, field, boost=1.0):
        if isinstance(query, FunctionScore):
            return self._compile_function_score_query(query, [field], boost)
        return super()._compile_query(query, field, boost)

    def _compile_function_score_query(self, query, fields, boost=1.0):
        if query.function_name == "script_score":
            params = query.function_params
        else:  # it's a decay query
            score_functions = {
                f.function_name: f for f in query.model_class.get_score_functions()
            }
            score_func = score_functions[query.function_name]

            # This is in place of get_field_column_name to build the name of the indexed field.
            remapped_field_name = score_func.get_score_name() + "_filter"
            params = {remapped_field_name: query.function_params["_field_name_"]}

        return {
            "function_score": {
                "query": self._join_and_compile_queries(query.subquery, fields, boost),
                query.function_name: params,
            }
        }


class CustomSearchMapping(
    FilteredSearchMapping,
): ...


class CustomSearchQueryCompiler(
    FunctionScoreSearchQueryCompiler,
    BoostSearchQueryCompiler,
    FilteredSearchQueryCompiler,
    OnlyFieldSearchQueryCompiler,
    NestedSearchQueryCompiler,
):
    mapping_class = CustomSearchMapping


class CustomAtomicIndexRebuilder(ElasticsearchAtomicIndexRebuilder):
    def start(self):
        index = super().start()
        build_queries_for_index(index)
        return index


class CustomSearchBackend(Elasticsearch7SearchBackend):
    query_compiler_class = CustomSearchQueryCompiler
    mapping_class = CustomSearchMapping
    atomic_rebuilder_class = CustomAtomicIndexRebuilder


SearchBackend = CustomSearchBackend
