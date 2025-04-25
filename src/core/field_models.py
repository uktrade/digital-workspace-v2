from django.db import models
from django.utils.html import strip_tags


class CharField(models.CharField):
    def clean(self, value, model_instance):
        return strip_tags(super().clean(value, model_instance))


# JSONField Need to test rich text and plain text in streamfields


class TextField(models.CharField):
    def clean(self, value, model_instance):
        return strip_tags(super().clean(value, model_instance))
