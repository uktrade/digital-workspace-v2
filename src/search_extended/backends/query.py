from wagtail.search.query import SearchQuery


class OnlyFields(SearchQuery):
    remapped_fields = None

    def __init__(self, subquery: SearchQuery, fields: list[str]):
        self.subquery = subquery
        self.fields = fields

    def __repr__(self):
        return "<OnlyFields {} fields=[{}]>".format(repr(self.subquery)," ".join([f"'{f}'" for f in self.fields]), )
