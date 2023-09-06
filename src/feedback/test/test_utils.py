import pytest
from django_feedback_govuk.models import BaseFeedback
from feedback.utils import feedback_received_within
from feedback.utils import send_feedback_notification


def test_no_feedback_submitted(db):
    # feedback_received_within() returns False if no feedback was submitted.
    assert not feedback_received_within()


def test_feedback_submitted_within_24hr_window(db):
    # feedback_received_within() returns True if feedback was submitted within the last 24hrs
    BaseFeedback.objects.create()
    assert feedback_received_within()


def test_feedback_submitted_over_24hrs_ago(db, freezer):
    # feedback_received_within() returns False if feedback was submitted over 24hrs ago
    freezer.move_to("2023-09-01")
    BaseFeedback.objects.create()

    freezer.move_to("2023-09-03")
    assert not feedback_received_within()


def test_send_feedback_notification_when_no_settings_are_set():
    # send_feedback_notification() raises an error when called with no settings provided
    with pytest.raises(Exception):
        send_feedback_notification()


def test_send_feedback_notification_with_no_email_recipients():
    # send_feedback_notification() raises an error when the email_recipients list is empty
    with pytest.raises(ValueError):
        send_feedback_notification()


# CASE 2: Method doesn't raise an error when it is called with valid settings (Django docs -> override_settings)
# def test_send_feedback_notification_with_valid_settings():
#     ...


# CASE 4: If the length is 1, then the send_email_notification method is called once (mock + mock.patch() + make sure all parameters included are correct)
# def test_send_feedback_email_notification_with_one_email_recipient():
#     ...


# CASE 5: If the length is more than 1, the send_email_notification method is called once
# per email address, test to make sure it is called with the expected data the expected number of times
# (this is the most complex test in this scenario so don't worry too much,
# I have to look at an example every time I write these types of tests)
