from datetime import timedelta

from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from django_feedback_govuk.models import BaseFeedback
from notifications_python_client.notifications import NotificationsAPIClient


def feedback_received_within(days=1):
    return BaseFeedback.objects.filter(
        submitted_at__gte=timezone.now() - timedelta(days=days)
    ).exists()


def send_feedback_notification():
    email_recipients = settings.FEEDBACK_NOTIFICATION_EMAIL_RECIPIENTS
    govuk_notify_template_id = settings.FEEDBACK_NOTIFICATION_EMAIL_TEMPLATE_ID
    base_url = settings.WAGTAILADMIN_BASE_URL
    notify_api_key = settings.GOVUK_NOTIFY_API_KEY

    if not all(
        [
            notify_api_key,
            govuk_notify_template_id,
            base_url,
            email_recipients,
        ]
    ):
        raise ValueError("Missing required settings for sending feedback notifications")

    if base_url[-1] == "/":
        base_url = base_url[:-1]

    notification_client = NotificationsAPIClient(
        settings.GOVUK_NOTIFY_API_KEY,
    )

    for email_recipient in email_recipients:
        notification_client.send_email_notification(
            email_address=email_recipient,
            template_id=govuk_notify_template_id,
            personalisation={"feedback_url": base_url + reverse("submitted-feedback")},
        )
