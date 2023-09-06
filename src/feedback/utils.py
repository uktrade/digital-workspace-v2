from django.utils import timezone
from django_feedback_govuk.models import BaseFeedback
from datetime import timedelta
from django.conf import settings
from notifications_python_client.notifications import NotificationsAPIClient
from django.urls import reverse


def feedback_received_within(days=1):
    return BaseFeedback.objects.filter(
        submitted_at__gte=timezone.now() - timedelta(days=days)
    ).exists()


def send_feedback_notification():
    if (
        settings.GOVUK_NOTIFY_API_KEY is None
        or settings.FEEDBACK_NOTIFICATION_EMAIL_RECIPIENTS is None
        or settings.FEEDBACK_NOTIFICATION_EMAIL_TEMPLATE_ID is None
        or settings.WAGTAILADMIN_BASE_URL is None
    ):
        raise TypeError("No settings provided")

    notification_client = NotificationsAPIClient(
        settings.GOVUK_NOTIFY_API_KEY,
    )
    email_recipients = settings.FEEDBACK_NOTIFICATION_EMAIL_RECIPIENTS
    govuk_notify_template_id = settings.FEEDBACK_NOTIFICATION_EMAIL_TEMPLATE_ID
    base_url = settings.WAGTAILADMIN_BASE_URL

    if len(email_recipients) < 1:
        raise ValueError("No feedback recipients configured")

    for email_recipient in email_recipients:
        notification_client.send_email_notification(
            email_address=email_recipient,
            template_id=govuk_notify_template_id,
            personalisation={"feedback_url": base_url + reverse("submitted-feedback")},
        )
    return
