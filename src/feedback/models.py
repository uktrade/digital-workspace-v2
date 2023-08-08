from django.db import models
from django_feedback_govuk.models import BaseFeedback, SatisfactionOptions


class SearchFeedbackV1(BaseFeedback):
    satisfaction = models.CharField(max_length=30, choices=SatisfactionOptions.choices)
    comment = models.TextField(blank=True)
