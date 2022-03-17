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


@shared_task
def person_created_updated_to_mailchimp_task(person: Person):
    notification_client = NotificationsAPIClient(settings.GOVUK_NOTIFY_API_KEY)
    try:
        mailchimp_handle_person(person)
    except Exception as create_update_error:
        notification_client.send_email_notification(
            email_address=settings.SUPPORT_REQUEST_EMAIL,
            template_id=settings.MERGE_MAILCHIMP_RESULT_TEMPLATE_ID,
            personalisation={
                "message": f"MailChimp create_update failed: {create_update_error}"
                f"for email f{person.contact_email}"
            },
        )
        raise create_update_error

    if settings.NOTIFY_MAILCHIMP_SUCCESS:
        notification_client.send_email_notification(
            email_address=settings.SUPPORT_REQUEST_EMAIL,
            template_id=settings.MERGE_MAILCHIMP_RESULT_TEMPLATE_ID,
            personalisation={
                "message": f"MailChimp create_update successful"
                f"for email f{person.contact_email}"
            },
        )


@shared_task
def person_deleted_to_mailchimp_task(person: Person):
    notification_client = NotificationsAPIClient(settings.GOVUK_NOTIFY_API_KEY)
    try:
        mailchimp_delete_person(person.contact_email)
    except Exception as delete_error:
        notification_client.send_email_notification(
            email_address=settings.SUPPORT_REQUEST_EMAIL,
            template_id=settings.MERGE_MAILCHIMP_RESULT_TEMPLATE_ID,
            personalisation={
                "message": f"MailChimp delete failed: {delete_error}"
                f"for email f{person.contact_email}"
            },
        )
        raise delete_error

    if settings.NOTIFY_MAILCHIMP_SUCCESS:
        notification_client.send_email_notification(
            email_address=settings.SUPPORT_REQUEST_EMAIL,
            template_id=settings.MERGE_MAILCHIMP_RESULT_TEMPLATE_ID,
            personalisation={
                "message": f"MailChimp delete_error successful"
                f"for email f{person.contact_email}"
            },
        )


@shared_task
def bulk_sync_task():
    partial_error = False
    notification_client = NotificationsAPIClient(settings.GOVUK_NOTIFY_API_KEY)
    try:
        # Bulk update Mailchimp with current People Finder data
        # We update Mailchimp at the relevant points in the `Person` model lifecycle, but this serves
        # as another line of defence against sync issues.

        try:
            message = create_or_update_subscriber_for_all_people()
        except MailchimpProcessingError:
            partial_error = True
        current_list = mailchimp_get_current_subscribers()
        delete_message = delete_subscribers_missing_locally(current_list)

    except Exception as bulk_error:
        notification_client.send_email_notification(
            email_address=settings.SUPPORT_REQUEST_EMAIL,
            template_id=settings.MERGE_MAILCHIMP_RESULT_TEMPLATE_ID,
            personalisation={
                "message": f"MailChimp bulk update failed: {bulk_error}; {message}; {delete_message}"
            },
        )
        raise bulk_error

    if partial_error or settings.NOTIFY_MAILCHIMP_BULK_SUCCESS:
        notification_client.send_email_notification(
            email_address=settings.SUPPORT_REQUEST_EMAIL,
            template_id=settings.MERGE_MAILCHIMP_RESULT_TEMPLATE_ID,
            personalisation={
                "message": f"MailChimp bulk update result: {message}; {delete_message}"
            },
        )
