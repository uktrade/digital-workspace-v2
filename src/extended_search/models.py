from django.db import models


class Setting(models.Model):
    """
    Holds settings for the search component; at the top priority level (i.e.
    able to supersede field definitions, ENV vars, configs etc)
    """

    key = models.CharField(
        max_length=200,
        help_text="'Flat key' of the setting",
        unique=True,
    )
    value = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Setting value",
    )

    class Meta:
        permissions = (
            ("view_explore", "View the global search explore page"),
            ("export_search", "Export the search result as csv"),
        )

    def __str__(self):
        return self.key
