from django_feedback_govuk.models import BaseFeedback
from feedback.utils import has_received_feedback_within_24hrs


def test_no_feedback_submitted(db):
    # has_received_feedback_within_24hrs() returns False if no feedback was submitted.
    assert not has_received_feedback_within_24hrs()

def test_feedback_submitted_within_24hr_window(db):
    # has_received_feedback_within_24hrs() returns True if feedback was submitted within the last 24hrs
    BaseFeedback.objects.create()
    assert has_received_feedback_within_24hrs()

def test_feedback_submitted_over_24hrs_ago(db, freezer):
    # has_received_feedback_within_24hrs() returns False if feedback was submitted over 24hrs ago
    freezer.move_to("2023-09-01")
    BaseFeedback.objects.create()

    freezer.move_to("2023-09-03")
    assert not has_received_feedback_within_24hrs()
