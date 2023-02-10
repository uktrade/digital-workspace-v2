from django.db import models
from simple_history.models import HistoricalRecords
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet


@register_snippet
class ExcludeFromSearch(models.Model):
    term = models.CharField(max_length=255)
    history = HistoricalRecords()

    def __str__(self):
        return self.term

    panels = [
        FieldPanel("term"),
    ]
