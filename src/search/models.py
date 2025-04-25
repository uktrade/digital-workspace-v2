from django.db import models
from simple_history.models import HistoricalRecords
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet

from core import field_models


@register_snippet
class ExcludeFromSearch(models.Model):
    term = field_models.CharField(max_length=255)
    history = HistoricalRecords()

    def __str__(self):
        return self.term

    panels = [
        FieldPanel("term"),
    ]
