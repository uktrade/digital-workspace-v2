import pytest
from unittest.mock import call
from django.test import override_settings
from django_feedback_govuk.models import BaseFeedback

from feedback.utils import feedback_received_within, send_feedback_notification


def test_no_feedback_submitted_and_feedback_submitted_within_24hrs(db):
    # feedback_received_within() returns False if no feedback was submitted and True if feedback was submitted within the last 24hrs.
    assert not feedback_received_within()
    BaseFeedback.objects.create()
    assert feedback_received_within()


def test_feedback_submitted_over_24hrs_ago(db, freezer):
    # feedback_received_within() returns False if feedback was submitted over 24hrs ago
    freezer.move_to("2023-09-01")
    BaseFeedback.objects.create()
    assert feedback_received_within()

    freezer.move_to("2023-09-03")
    assert not feedback_received_within()


@override_settings(
    GOVUK_NOTIFY_API_KEY=None,
    FEEDBACK_NOTIFICATION_EMAIL_TEMPLATE_ID=None,
    WAGTAILADMIN_BASE_URL=None,
)
def test_send_feedback_notification_when_no_settings_are_set():
    # send_feedback_notification() raises an error when called with no settings provided
    with pytest.raises(ValueError) as raised_execption:
        send_feedback_notification()
        assert (
            raised_execption.value.args[0]
            == "Missing required settings for sending feedback notifications"
        )


@override_settings(
    GOVUK_NOTIFY_API_KEY="test-api-key",
    FEEDBACK_NOTIFICATION_EMAIL_RECIPIENTS=[],
    FEEDBACK_NOTIFICATION_EMAIL_TEMPLATE_ID="test-template-id",
    WAGTAILADMIN_BASE_URL="https://test.example.com/",
)
def test_send_feedback_notification_with_no_email_recipients():
    # send_feedback_notification() raises an error when the email_recipients list is empty
    with pytest.raises(ValueError) as raised_exception:
        send_feedback_notification()
        assert (
            raised_exception.value.args[0]
            == "Missing required settings for sending feedback notifications"
        )


@override_settings(
    GOVUK_NOTIFY_API_KEY="this-is-my-really-long-api-key-because-gov-uk-notify-expects-it-to-be-long-when-you-create-a-service",
    FEEDBACK_NOTIFICATION_EMAIL_RECIPIENTS=["test@email.com"],
    FEEDBACK_NOTIFICATION_EMAIL_TEMPLATE_ID="test-template-id",
    WAGTAILADMIN_BASE_URL="https://test.example.com/",
)
def test_send_feedback_notification_with_valid_settings(mocker):
    # send_feedback_notification() does not raise an error when all the settings provided are valid
    mock_send_email_notification = mocker.patch(
        "feedback.utils.NotificationsAPIClient.send_email_notification"
    )
    send_feedback_notification()
    mock_send_email_notification.assert_called_once_with(
        email_address="test@email.com",
        template_id="test-template-id",
        personalisation={
            "feedback_url": "https://test.example.com/feedback/submitted/"
        },
    )


@override_settings(
    GOVUK_NOTIFY_API_KEY="this-is-my-really-long-api-key-because-gov-uk-notify-expects-it-to-be-long-when-you-create-a-service",
    FEEDBACK_NOTIFICATION_EMAIL_RECIPIENTS=["test1@email.com", "test2@email.com"],
    FEEDBACK_NOTIFICATION_EMAIL_TEMPLATE_ID="test-template-id",
    WAGTAILADMIN_BASE_URL="https://test.example.com/",
)
def test_send_feedback_notification_with_multiple_emails(mocker):
    # send_email_notification() is called once per email address
    mock_send_email_notification = mocker.patch(
        "feedback.utils.NotificationsAPIClient.send_email_notification"
    )
    expected_calls = [
        call(
            email_address="test1@email.com",
            template_id="test-template-id",
            personalisation={
                "feedback_url": "https://test.example.com/feedback/submitted/"
            },
        ),
        call(
            email_address="test2@email.com",
            template_id="test-template-id",
            personalisation={
                "feedback_url": "https://test.example.com/feedback/submitted/"
            },
        ),
    ]
    send_feedback_notification()
    assert mock_send_email_notification.call_count == len(expected_calls)
    mock_send_email_notification.assert_has_calls(expected_calls)
