from django.utils import timezone
from django_feedback_govuk.models import BaseFeedback
from datetime import timedelta
from django.conf import settings
from notifications_python_client.notifications import NotificationsAPIClient


def is_feedback_received_past_24hrs():
    current_datetime = timezone.now()
    time_difference = timedelta(days=1)
    is_feedback_received = BaseFeedback.objects.filter(
        submitted_at__gte=current_datetime - time_difference
    ).exists()
    return is_feedback_received


def send_feedback_notification():
    notification_client = NotificationsAPIClient(
        settings.GOVUK_NOTIFY_API_KEY,
    )
    email_recipients = settings.FEEDBACK_NOTIFICATION_EMAIL_RECIPIENTS

    if len(email_recipients) < 1:
        raise Exception("No feedback recipients configured")

    for email_recipient in email_recipients:
        message = notification_client.send_email_notification(
            email_address = email_recipient,
            template_id = settings.FEEDBACK_NOTIFICATION_EMAIL_TEMPLATE_ID,
            personalisation = {
                # TODO: if email template has dynamic content add key-values pair here
            },
        )

    return message