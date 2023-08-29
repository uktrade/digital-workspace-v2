from django_feedback_govuk.models import BaseFeedback
from datetime import datetime, timedelta

def get_feedback_submitted_past_24hrs():
    current_datetime = datetime.now()
    time_difference = timedelta(days=1)
    feedback_past_24hrs = BaseFeedback.objects.filter(submitted_at__gte = current_datetime - time_difference)
    return feedback_past_24hrs