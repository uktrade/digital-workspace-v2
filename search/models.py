from django.db import models
from wagtail.admin.edit_handlers import (
    FieldPanel,
)
from wagtail.snippets.models import register_snippet


@register_snippet
class ExcludeFromSearch(models.Model):
    term = models.CharField(max_length=255)

    def __str__(self):
        return self.term

    panels = [
        FieldPanel("term"),
    ]
