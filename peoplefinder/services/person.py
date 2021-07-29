import logging

from django.conf import settings
from django.http import HttpRequest
from django.shortcuts import reverse
from notifications_python_client.notifications import NotificationsAPIClient

from peoplefinder.models import Person


logger = logging.getLogger(__name__)

LOG_MESSAGE = """People Finder deletion request: {profile_name}

Profile deletion request

Profile name: {profile_name}
Profile URL: {profile_url}

Reporter by: {reporter_name}
Reporter email: {reporter_email}

Note: {comment}
"""


class PersonService:
    def left_dit(
        self, request: HttpRequest, person: Person, reported_by: Person, comment: str
    ) -> None:
        """Submit that the given person has left the DIT.

        Args:
            request: The associated HTTP request.
            person: The person who has left the DIT.
            reported_by: Who reported that the person has left.
            comment: A comment from the reporter about the request.
        """
        context = {
            "profile_name": person.full_name,
            "profile_url": request.build_absolute_uri(
                reverse("profile-view", kwargs={"profile_pk": person.user_id})
            ),
            "reporter_name": reported_by.full_name,
            "reporter_email": reported_by.preferred_email,
            "comment": comment,
        }

        if settings.APP_ENV in ("local", "test"):
            logger.info(LOG_MESSAGE.format(**context))

            return

        notification_client = NotificationsAPIClient(settings.GOVUK_NOTIFY_API_KEY)
        notification_client.send_email_notification(
            settings.PROFILE_DELETION_REQUEST_EMAIL,
            settings.PROFILE_DELETION_REQUEST_EMAIL_TEMPLATE_ID,
            context,
        )
