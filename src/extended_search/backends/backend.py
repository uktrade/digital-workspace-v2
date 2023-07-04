from wagtail.search.backends.elasticsearch7 import (
    Elasticsearch7SearchBackend,
    Elasticsearch7SearchQueryCompiler,
    Elasticsearch7Mapping,
)
from wagtail.search.query import MATCH_NONE, Fuzzy, MatchAll, Phrase, PlainText

from extended_search.backends.query import OnlyFields


class ExtendedSearchQueryCompiler(Elasticsearch7SearchQueryCompiler):
    """
    Acting as a placeholder for upstream merges to Wagtail in a PR; this class
    doesn't change any behaviour but instead assigns responsibility for
    particular aspects to smaller methods to make it easier to override. In the
    PR maybe worth referencing https://github.com/wagtail/wagtail/issues/5422
    """

    # def __init__(self, *args, **kwargs):
    #     """
    #     This override doesn't do anything, it's just here as a reminder to
    #     modify the underlying class in this way when creating the upstream PR
    #     """
    #     super().__init__(*args, **kwargs)
    #     self.mapping = self.mapping_class(self.queryset.model)
    #     self.remapped_fields = self._remap_fields(self.fields)

    def _remap_fields(self, fields):
        """
        Convert field names into index column names
        """
        if fields is None:
            return None

        remapped_fields = []
        searchable_fields = {
            f.field_name: f for f in self.queryset.model.get_searchable_search_fields()
        }
        for field_name in fields:
            if field_name in searchable_fields:
                field_name = self.mapping.get_field_column_name(
                    searchable_fields[field_name]
                )

            remapped_fields.append(field_name)

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

    def get_inner_query(self):
        """
        This is a brittle override of the Elasticsearch7SearchQueryCompiler.
        get_inner_query, acting as a standin for getting these changes merged
        upstream. It exists in order to break out the _join_and_compile_queries
        method
        """
        if self.remapped_fields:
            fields = self.remapped_fields
        elif self.partial_match:
            fields = [self.mapping.all_field_name, self.mapping.edgengrams_field_name]
        else:
            fields = [self.mapping.all_field_name]

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

        else:
            return self._join_and_compile_queries(self.query, fields)


# JUST FOR DEBUGGING WHAT WAGTAIL DOES
# -----------------------------------------------------------------
#

# import inspect

# from wagtail.search.index import (
#     AutocompleteField,
#     FilterField,
#     RelatedFields,
#     SearchField,
# )


# def get_model_root(model):
#     """
#     This function finds the root model for any given model. The root model is
#     the highest concrete model that it descends from. If the model doesn't
#     descend from another concrete model then the model is it's own root model so
#     it is returned.

#     Examples:
#     >>> get_model_root(wagtailcore.Page)
#     wagtailcore.Page

#     >>> get_model_root(myapp.HomePage)
#     wagtailcore.Page

#     >>> get_model_root(wagtailimages.Image)
#     wagtailimages.Image
#     """
#     if model._meta.parents:
#         parent_model = list(model._meta.parents.items())[0][0]
#         return get_model_root(parent_model)

#     return model


class DebugMapping(Elasticsearch7Mapping):
    def get_field_column_name(self, field):
        return super().get_field_column_name(field)


#     def get_field_mapping(self, field):
#         if isinstance(field, RelatedFields):
#             return super().get_field_mapping(field)
#         else:
#             mapping = {"type": self.type_map.get(field.get_type(self.model), "string")}

#             if isinstance(field, SearchField):
#                 if mapping["type"] == "string":
#                     mapping["type"] = self.text_type

#                 if field.boost:
#                     mapping["boost"] = field.boost

#                 if field.partial_match:
#                     mapping.update(self.edgengram_analyzer_config)

#                 mapping["include_in_all"] = True

#             if isinstance(field, AutocompleteField):
#                 mapping["type"] = self.text_type
#                 mapping["include_in_all"] = False
#                 mapping.update(self.edgengram_analyzer_config)

#             elif isinstance(field, FilterField):
#                 if mapping["type"] == "string":
#                     mapping["type"] = self.keyword_type

#                 if self.set_index_not_analyzed_on_filter_fields:
#                     # Not required on ES5 as that uses the "keyword" type for
#                     # filtered string fields
#                     mapping["index"] = "not_analyzed"

#                 mapping["include_in_all"] = False

#             if "es_extra" in field.kwargs:
#                 for key, value in field.kwargs["es_extra"].items():
#                     mapping[key] = value

#             curframe = inspect.currentframe()
#             calframe = inspect.getouterframes(curframe, 2)
#             print(f"-> gfm:: {field}: {isinstance(field, SearchField)}, {mapping}")
#             print(f"    {calframe[1][3]} ({calframe[1][1]}:{calframe[1][2]})")

#             return self.get_field_column_name(field), mapping


#     def get_field_column_name(self, field):
#         # Fields in derived models get prefixed with their model name, fields
#         # in the root model don't get prefixed at all
#         # This is to prevent mapping clashes in cases where two page types have
#         # a field with the same name but a different type.
#         root_model = get_model_root(self.model)
#         definition_model = field.get_definition_model(self.model)

#         curframe = inspect.currentframe()
#         calframe = inspect.getouterframes(curframe, 2)
#         print(f">>>>>>>>> {root_model} <> {field} | {self.model} <> {definition_model} <<<<<<<<<<")
#         print(f"    {calframe[1][3]} ({calframe[1][1]}:{calframe[1][2]})")

#         if definition_model != root_model:
#             prefix = (
#                 definition_model._meta.app_label.lower()
#                 + "_"
#                 + definition_model.__name__.lower()
#                 + "__"
#             )
#         else:
#             prefix = ""

#         if isinstance(field, FilterField):
#             return prefix + field.get_attname(self.model) + "_filter"
#         elif isinstance(field, AutocompleteField):
#             return prefix + field.get_attname(self.model) + "_edgengrams"
#         elif isinstance(field, SearchField):
#             return prefix + field.get_attname(self.model)
#         elif isinstance(field, RelatedFields):
#             return prefix + field.field_name


#
# OK back to real stuff
# -----------------------------------------------------------------
#


class OnlyFieldSearchQueryCompiler(ExtendedSearchQueryCompiler):
    """
    Acting as a placeholder for upstream merges to Wagtail in a separate PR to
    the ExtendedSearchQueryCompiler; this exists to support the new OnlyFields
    SearchQuery
    """

    mapping_class = DebugMapping

    def _compile_query(self, query, field, boost=1.0):
        """
        Override the parent method to handle specifics of the OnlyFields
        SearchQuery
        """
        if not isinstance(query, OnlyFields):
            return super()._compile_query(query, field, boost)

        remapped_fields = self._remap_fields(query.fields)

        if field == self.mapping.all_field_name:
            # We are using the "_all_text" field proxy (i.e. the search()
            # method was called without the fields kwarg), but now we want to
            # limit the downstream fields compiled to those explicitly defined
            # in the OnlyFields query
            return self._join_and_compile_queries(
                query.subquery, remapped_fields, boost
            )

        elif field in remapped_fields:
            # Fields were defined explicitly upstream, and we are dealing with
            # one that's in the OnlyFields filter
            return self._compile_query(query.subquery, field, boost)

        else:
            # Exclude this field from any further downstream compilation: it
            # was defined in the search() method but has been excluded from
            # this part of the tree with an OnlyFields filter
            return self._compile_query(MATCH_NONE, field, boost)


class CustomSearchBackend(Elasticsearch7SearchBackend):
    query_compiler_class = OnlyFieldSearchQueryCompiler
    mapping_class = DebugMapping


SearchBackend = CustomSearchBackend
