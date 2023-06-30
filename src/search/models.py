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


class SearchSettings(models.Model):
    class Meta:
        # No database table creation or deletion operations will be performed
        # for this model.
        managed = False

        # disable "add", "change", "delete" and "view" default permissions
        default_permissions = ()

        permissions = (
            ("change_boost", "Edit boost settings for search components"),
            ("view_explore", "View the global search explore page"),
        )
