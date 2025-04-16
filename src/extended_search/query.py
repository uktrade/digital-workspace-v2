from typing import Optional

from django.db import models
from wagtail.search.query import SearchQuery


class Nested(SearchQuery):
    def __init__(self, subquery: SearchQuery, path: str):
        if not isinstance(subquery, SearchQuery):
            raise TypeError("The `subquery` parameter must be of type SearchQuery")

        if not isinstance(path, str):
            raise TypeError("The `path` parameter must be a string")

        self.subquery = subquery
        self.path = path

    def __repr__(self):
        return "<Nested {} path='{}'>".format(
            repr(self.subquery),
            self.path,
        )


class OnlyFields(SearchQuery):
    remapped_fields = None

    def __init__(
        self, subquery: SearchQuery, fields: list[str], only_model: models.Model
    ):
        if not isinstance(subquery, SearchQuery):
            raise TypeError("The `subquery` parameter must be of type SearchQuery")

        if not isinstance(fields, list):
            raise TypeError("The `fields` parameter must be a list")

        self.subquery = subquery
        self.only_model = only_model
        self.fields = fields

    def __repr__(self):
        return "<OnlyFields {} fields=[{}]>".format(
            repr(self.subquery),
            ", ".join([f"'{f}'" for f in self.fields]),
        )


class Filtered(SearchQuery):
    def __init__(self, subquery: SearchQuery, filters: list[tuple]):
        if not isinstance(subquery, SearchQuery):
            raise TypeError("The `subquery` parameter must be of type SearchQuery")

        if not isinstance(filters, list):
            raise TypeError("The `filters` parameter must be a list of thruples")

        if not isinstance(filters[0], tuple) or not len(filters[0]) == 3:
            raise TypeError("The `filters` parameter must be a list of thruples")

        self.subquery = subquery
        self.filters = filters

    def __repr__(self):
        return "<Filtered {} filters=[{}]>".format(
            repr(self.subquery),
            ", ".join([f"{f}" for f in self.filters]),
        )


class FunctionScore(SearchQuery):
    remapped_fields = None

    def __init__(
        self,
        model_class: models.Model,
        subquery: SearchQuery,
        function_name: str,
        function_params: dict,
        field: Optional[str] = None,
    ):
        if not isinstance(subquery, SearchQuery):
            raise TypeError("The `subquery` parameter must be of type SearchQuery")

        if not isinstance(function_name, str):
            raise TypeError("The `function_name` parameter must be a string")

        if not isinstance(function_params, dict):
            raise TypeError("The `function_params` parameter must be a dict")

        if field is not None and not isinstance(field, str):
            raise TypeError("The `field` parameter must be a string")

        self.model_class = model_class
        self.subquery = subquery
        self.function_name = function_name
        self.function_params = function_params
        self.field = field

    def __repr__(self):
        return "<FunctionScore {} function_name='{}' function_params='{}' field='{}' >".format(
            repr(self.subquery),
            self.function_name,
            self.function_params,
            self.field,
        )
