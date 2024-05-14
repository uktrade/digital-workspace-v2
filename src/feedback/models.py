from django.db import models
from django_feedback_govuk.models import BaseFeedback, SatisfactionOptions


class HRFeedback(BaseFeedback):
    page_url = models.CharField(blank=True)
    useful = models.BooleanField(default=True)
    contactable = models.BooleanField(default=False)
    comment = models.TextField(blank=True)


class SearchFeedbackV1(BaseFeedback):
    satisfaction = models.CharField(max_length=30, choices=SatisfactionOptions.choices)
    comment = models.TextField(blank=True)


class SearchFeedbackV2(BaseFeedback):
    search_query = models.CharField(max_length=255)
    useful = models.BooleanField(default=True)

    not_useful_comment = models.TextField(blank=True)
    trying_to_find = models.TextField(blank=True)

    search_data = models.JSONField(blank=True, null=True, default=dict)
