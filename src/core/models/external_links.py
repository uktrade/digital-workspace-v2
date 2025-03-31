from django.db import models


class ExternalLinkSetting(models.Model):
    class Meta:
        unique_together = (("domain", "exclude"),)

    domain = models.CharField(
        max_length=255,
        help_text="The domain to match for this setting (example: gov.uk).",
    )
    exclude = models.BooleanField(
        default=False,
        help_text="Don't show the external link text for this domain.",
    )
    external_link_text = models.CharField(
        max_length=255,
        help_text="The text to show for this domain (example: GOV UK).",
        blank=True,
    )

    def __str__(self):
        if self.exclude:
            return f"{self.domain} (excluded)"
        return f"{self.domain} - {self.external_link_text}"
