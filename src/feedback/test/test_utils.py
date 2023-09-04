from django_feedback_govuk.models import BaseFeedback
from feedback.utils import feedback_received_within


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
