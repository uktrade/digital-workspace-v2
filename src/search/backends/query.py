from wagtail.search.query import MATCH_NONE, SearchQuery


class Only(SearchQuery):
    def __init__(self, subquery: SearchQuery, boost: float, fields: list[str]):
        self.subquery = subquery
        self.boost = boost
        self.fields = fields

    def __repr__(self):
        return "<Only {} >".format(repr(self.subquery))
