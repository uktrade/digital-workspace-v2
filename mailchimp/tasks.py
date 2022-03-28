from celery import shared_task
from django.conf import settings
from mailchimp.services import (
    MailchimpProcessingError,
    create_or_update_subscriber_for_all_people,
    delete_subscribers_missing_locally,
    mailchimp_delete_person,
    mailchimp_get_current_subscribers,
    mailchimp_handle_person,
)
from notifications_python_client.notifications import NotificationsAPIClient

from peoplefinder.models import Person


class MailChimpPartialError(Exception):
    pass


@shared_task
def person_created_or_updated(id: int):
    if not settings.MAILCHIMP_UPDATE:
        return

    person = Person.objects.get(pk=id)
    notification_client = NotificationsAPIClient(settings.GOVUK_NOTIFY_API_KEY)

    try:
        mailchimp_handle_person(person)
    except Exception as create_update_error:
        notification_client.send_email_notification(
            email_address=settings.SUPPORT_REQUEST_EMAIL,
            template_id=settings.MERGE_MAILCHIMP_RESULT_TEMPLATE_ID,
            personalisation={
                "message": f"MailChimp create_update failed: {create_update_error}"
                f"for email f{person.email}"
            },
        )
        raise create_update_error

    if settings.NOTIFY_MAILCHIMP_SUCCESS:
        notification_client.send_email_notification(
            email_address=settings.SUPPORT_REQUEST_EMAIL,
            template_id=settings.MERGE_MAILCHIMP_RESULT_TEMPLATE_ID,
            personalisation={
                "message": f"MailChimp create_update successful"
                f"for email f{person.email}"
            },
        )


@shared_task
def person_deleted(id: int):
    if not settings.MAILCHIMP_UPDATE:
        return

    person = Person.objects.get(pk=id)
    notification_client = NotificationsAPIClient(settings.GOVUK_NOTIFY_API_KEY)

    try:
        mailchimp_delete_person(person.email)
    except Exception as delete_error:
        notification_client.send_email_notification(
            email_address=settings.SUPPORT_REQUEST_EMAIL,
            template_id=settings.MERGE_MAILCHIMP_RESULT_TEMPLATE_ID,
            personalisation={
                "message": f"MailChimp delete failed: {delete_error}"
                f"for email f{person.email}"
            },
        )
        raise delete_error

    if settings.NOTIFY_MAILCHIMP_SUCCESS:
        notification_client.send_email_notification(
            email_address=settings.SUPPORT_REQUEST_EMAIL,
            template_id=settings.MERGE_MAILCHIMP_RESULT_TEMPLATE_ID,
            personalisation={
                "message": f"MailChimp delete_error successful"
                f"for email f{person.email}"
            },
        )


@shared_task
def bulk_sync_task():
    notification_client = NotificationsAPIClient(settings.GOVUK_NOTIFY_API_KEY)
    try:
        # Bulk update Mailchimp with current People Finder data
        # We update Mailchimp at the relevant points in the `Person` model lifecycle, but this serves
        # as another line of defence against sync issues.
        message = create_or_update_subscriber_for_all_people()
        current_list = mailchimp_get_current_subscribers()
        delete_message = delete_subscribers_missing_locally(current_list)

    except Exception as bulk_error:
        notification_client.send_email_notification(
            email_address=settings.SUPPORT_REQUEST_EMAIL,
            template_id=settings.MERGE_MAILCHIMP_RESULT_TEMPLATE_ID,
            personalisation={
                "message": f"MailChimp bulk update failed: {bulk_error} Check sentry for more details"
            },
        )
        if isinstance(bulk_error, MailchimpProcessingError):
            msg = (
                f"{bulk_error}, "
                f"update person response: {bulk_error.response}, "
                f"update tag response: {bulk_error.response_tag}"
            )
            raise MailChimpPartialError(msg)
        else:
            raise bulk_error

    if settings.NOTIFY_MAILCHIMP_BULK_SUCCESS:
        notification_client.send_email_notification(
            email_address=settings.SUPPORT_REQUEST_EMAIL,
            template_id=settings.MERGE_MAILCHIMP_RESULT_TEMPLATE_ID,
            personalisation={
                "message": f"MailChimp bulk update result: {message}; {delete_message}"
            },
        )
