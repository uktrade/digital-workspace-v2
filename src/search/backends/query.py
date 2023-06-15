from wagtail.search.query import MATCH_NONE, SearchQuery


class Only(SearchQuery):
    remapped_fields = []

    def __init__(self, subquery: SearchQuery, fields: list[str]):
        self.subquery = subquery
        self.fields = fields

    def __repr__(self):
        return "<Only {} >".format(repr(self.subquery))
