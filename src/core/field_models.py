from django.db import models
from django.utils.html import strip_tags


class CharField(models.CharField):
    def clean(self, value, model_instance):
        cleaned_value = super().clean(value, model_instance)

        if not self.choices:
            return strip_tags(cleaned_value)

        return cleaned_value


# JSONField Need to test rich text and plain text in streamfields


class TextField(models.TextField):
    def clean(self, value, model_instance):
        cleaned_value = super().clean(value, model_instance)

        if not self.choices:
            return strip_tags(cleaned_value)

        return cleaned_value
