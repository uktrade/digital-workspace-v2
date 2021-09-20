import logging

from django.conf import settings
from django.http import HttpRequest
from django.shortcuts import reverse
from notifications_python_client.notifications import NotificationsAPIClient

from peoplefinder.models import AuditLog, Person
from peoplefinder.services.audit_log import AuditLogService
from user.models import User


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
    def create_user_profile(self, user: User) -> Person:
        """Create a profile for the given user if there isn't one.

        Args:
            user: The given user.

        Returns:
            The user's profile.
        """
        if hasattr(user, "profile"):
            return user.profile

        person = Person.objects.create(
            user=user,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
        )

        self.profile_created(person, user)

        return person

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
                reverse("profile-view", kwargs={"profile_slug": person.slug})
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

    def profile_created(self, person: Person, created_by: User) -> None:
        """A method to be called after a profile has been created.

        Please don't forget to call method this unless you need to bypass it.

        This is the main hook for calling out to other processes which need to happen
        after a profile has been created.

        Args:
            person: The person behind the profile.
            created_by: The user which created the profile.
        """
        AuditLogService().log(AuditLog.Action.CREATE, created_by, person)

    def profile_updated(self, person: Person, updated_by: User) -> None:
        """A method to be called after a profile has been updated.

        Please don't forget to call method this unless you need to bypass it.

        This is the main hook for calling out to other processes which need to happen
        after a profile has been updated.

        Args:
            person: The person behind the profile.
            updated_by: The user which updated the profile.
        """
        AuditLogService().log(AuditLog.Action.UPDATE, updated_by, person)

    def profile_deleted(self, person: Person, deleted_by: User) -> None:
        """A method to be called after a profile has been deleted.

        Please don't forget to call method this unless you need to bypass it.

        This is the main hook for calling out to other processes which need to happen
        after a profile has been deleted.

        Args:
            person: The person behind the profile.
            deleted_by: The user which deleted the profile.
        """
        raise NotImplementedError
