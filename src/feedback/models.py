from django.db import models
from django_feedback_govuk.models import BaseFeedback, SatisfactionOptions

from core import field_models


class HRFeedback(BaseFeedback):
    page_url = field_models.CharField(blank=True)
    useful = models.BooleanField(default=True)
    contactable = models.BooleanField(default=False)
    comment = field_models.TextField(blank=True)


class SearchFeedbackV1(BaseFeedback):
    satisfaction = field_models.CharField(
        max_length=30, choices=SatisfactionOptions.choices
    )
    comment = field_models.TextField(blank=True)


class SearchFeedbackV2(BaseFeedback):
    search_query = field_models.CharField(max_length=255)
    useful = models.BooleanField(default=True)

    not_useful_comment = field_models.TextField(blank=True)
    trying_to_find = field_models.TextField(blank=True)

    search_data = models.JSONField(blank=True, null=True, default=dict)
