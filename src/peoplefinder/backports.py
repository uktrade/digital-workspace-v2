from django.contrib.postgres.fields import ArrayField
from django.db.models import Subquery
from django.utils.functional import cached_property


# Backport of Django's Postgres specific ArraySubquery expression.
# Documentation: https://docs.djangoproject.com/en/dev/ref/contrib/postgres/expressions/#arraysubquery-expressions
# Commit: https://github.com/django/django/commit/a06b977a91f043c509df781670fb4cf35cb437b7 /PS-IGNORE
# TODO: Remove once Django has released this and we upgrade to that version.
class ArraySubquery(Subquery):
    template = "ARRAY(%(subquery)s)"

    def __init__(self, queryset, **kwargs):
        super().__init__(queryset, **kwargs)

    @cached_property
    def output_field(self):
        return ArrayField(self.query.output_field)
