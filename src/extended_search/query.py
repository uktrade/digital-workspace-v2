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

    def __init__(self, subquery: SearchQuery, fields: list[str]):
        if not isinstance(subquery, SearchQuery):
            raise TypeError("The `subquery` parameter must be of type SearchQuery")

        if not isinstance(fields, list):
            raise TypeError("The `fields` parameter must be a list")

        self.subquery = subquery
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
