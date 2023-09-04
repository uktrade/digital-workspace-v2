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
    notification_client = NotificationsAPIClient(
        settings.GOVUK_NOTIFY_API_KEY,
    )
    email_recipients = settings.FEEDBACK_NOTIFICATION_EMAIL_RECIPIENTS

    if len(email_recipients) < 1:
        raise Exception("No feedback recipients configured")

    for email_recipient in email_recipients:
        message = notification_client.send_email_notification(
            email_address=email_recipient,
            template_id=settings.FEEDBACK_NOTIFICATION_EMAIL_TEMPLATE_ID,
            personalisation={
                "feedback_url": settings.WAGTAIL_BASE_URL
                + reverse("submitted-feedback")
            },
        )

    return message
