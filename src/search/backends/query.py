from wagtail.search.query import MATCH_NONE, SearchQuery


class OnlyFields(SearchQuery):
    remapped_fields = None

    def __init__(self, subquery: SearchQuery, fields: list[str]):
        self.subquery = subquery
        self.fields = fields

    def __repr__(self):
        return "<OnlyFields {} >".format(repr(self.subquery))
