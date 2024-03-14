from django.db import models
from simple_history import register
from wagtail.documents.models import Document
from waffle.models import AbstractUserFlag


register(Document, app=__package__)


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
