from django.core.exceptions import ValidationError
from django.db import models
from simple_history import register
from simple_history.models import HistoricalRecords
from waffle.models import AbstractUserFlag
from wagtail.documents.models import Document
from wagtail.snippets.models import register_snippet


@register_snippet
class SiteAlertBanner(models.Model):
    banner_text = models.CharField(max_length=255)
    banner_link = models.CharField(
        max_length=255,
        blank=True,
        null=True,
    )
    activated = models.BooleanField(
        default=False,
    )
    history = HistoricalRecords()

    def __str__(self):
        return self.banner_text

    def clean(self):
        activated_banner = SiteAlertBanner.objects.filter(
            activated=True,
        ).first()

        if activated_banner and self.id != activated_banner.id and self.activated:
            raise ValidationError(
                "You can only have one active banner at a time. "
                f"Currently the '{activated_banner}' banner is active"
            )


register(Document, "core")


class IngestedModelManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class IngestedModel(models.Model):
    class Meta:
        abstract = True

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    objects = IngestedModelManager()


class FeatureFlag(AbstractUserFlag):
    pass
