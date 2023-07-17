from wagtail.search.query import SearchQuery


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
