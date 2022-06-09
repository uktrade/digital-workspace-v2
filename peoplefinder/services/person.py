import logging
from typing import Optional

from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Case, F, Q, Value, When
from django.db.models.functions import Concat
from django.http import HttpRequest
from django.shortcuts import reverse
from django.utils import timezone
from notifications_python_client.notifications import NotificationsAPIClient

from peoplefinder.management.commands.create_people_finder_groups import (
    PERSON_ADMIN_GROUP_NAME,
    TEAM_ADMIN_GROUP_NAME,
)
from peoplefinder.models import AuditLog, Person
from peoplefinder.services.audit_log import (
    AuditLogSerializer,
    AuditLogService,
    ObjectRepr,
)
from user.models import User


logger = logging.getLogger(__name__)

LEFT_DIT_LOG_MESSAGE = """People Finder deletion request: {profile_name}

Profile deletion request

Profile name: {profile_name}
Profile URL: {profile_url}

Reporter by: {reporter_name}
Reporter email: {reporter_email}

Note: {comment}
"""

NOTIFY_ABOUT_CHANGES_LOG_MESSAGE = """Hello {profile_name},

{editor_name} has made changes to your profile on Digital Workspace.

You may want to check your profile to make sure that it is up to date:
{profile_url}

You can update any profile on Digital Workspace. Find out more at: https://workspace.trade.gov.uk/working-at-dit/policies-and-guidance/using-people-finder/
"""


class PersonService:
    def create_user_profile(self, user: User) -> Person:
        """Create a profile for the given user if there isn't one.

        Args:
            user: The given user.

        Returns:
            The user's profile.
        """
        # The user already has a profile.
        if hasattr(user, "profile"):
            user.profile.login_count += 1
            user.profile.save()

            return user.profile

        # The user doesn't have a profile, so let's try and find a matching one.
        get_queries = [
            # First see if we can match on the legacy SSO ID.
            Q(legacy_sso_user_id=user.legacy_sso_user_id),
            # Next see if we can match on the email.
            Q(email=user.email),
            # Finally try and match on the first and last name. # /PS-IGNORE
            Q(first_name=user.first_name, last_name=user.last_name),
        ]

        for query in get_queries:
            try:
                person = Person.objects.get(Q(user__isnull=True) & query)
            except (Person.DoesNotExist, Person.MultipleObjectsReturned):
                person = None
            else:
                break

        # If we found a matching profile, update and return it.
        if person:
            person.user = user
            person.login_count += 1
            person.save()

            return person

        # We couldn't find a matching one so let's create one for them.
        person = Person.objects.create(
            user=user,
            legacy_sso_user_id=user.legacy_sso_user_id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            login_count=1,
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
            logger.info(LEFT_DIT_LOG_MESSAGE.format(**context))

            return

        notification_client = NotificationsAPIClient(settings.GOVUK_NOTIFY_API_KEY)
        notification_client.send_email_notification(
            settings.PROFILE_DELETION_REQUEST_EMAIL,
            settings.PROFILE_DELETION_REQUEST_EMAIL_TEMPLATE_ID,
            personalisation=context,
        )

    def profile_created(self, person: Person, created_by: Optional[User]) -> None:
        """A method to be called after a profile has been created.

        Please don't forget to call method this unless you need to bypass it.

        This is the main hook for calling out to other processes which need to happen
        after a profile has been created.

        Args:
            person: The person behind the profile.
            created_by: The user which created the profile.
        """
        AuditLogService().log(AuditLog.Action.CREATE, created_by, person)

    def profile_updated(
        self, request: Optional[HttpRequest], person: Person, updated_by: User
    ) -> None:
        """A method to be called after a profile has been updated.

        Please don't forget to call method this unless you need to bypass it.

        This is the main hook for calling out to other processes which need to happen
        after a profile has been updated.

        Only pass `None` for `request` when the action is made outside a web request,
        i.e, in a management command.

        Args:
            request: The HTTP request related to the action.
            person: The person behind the profile.
            updated_by: The user which updated the profile.
        """
        AuditLogService().log(AuditLog.Action.UPDATE, updated_by, person)

        if request:
            person.edited_or_confirmed_at = timezone.now()
            person.save()

            self.notify_about_changes(request, person)

    def profile_deletion_initiated(
        self, request: Optional[HttpRequest], person: Person, initiated_by: User
    ) -> None:
        """
        Args:
            request: The HTTP request related to the action.
            person: The person behind the profile.
            initiated_by: The user which initiated the deletion.
        """

        self.notify_about_deletion(person, initiated_by)

    def profile_deleted(
        self, request: Optional[HttpRequest], person: Person, deleted_by: User
    ) -> None:
        """
        This is the main hook for calling out to other processes which need to
        happen after a profile has been deleted. Please don't forget to call this
        method unless you need to bypass it.

        Args:
            request: The HTTP request related to the action.
            person: The person behind the profile.
            deleted_by: The user which deleted the profile.
        """
        person.is_active = False
        person.became_inactive = timezone.now()
        person.save()

        AuditLogService().log(AuditLog.Action.DELETE, deleted_by, person)

        if request:
            self.notify_about_deletion(person, deleted_by)

    def notify_about_changes(self, request: HttpRequest, person: Person) -> None:
        editor = request.user.profile

        if editor == person:
            return None

        context = {
            "profile_name": person.full_name,
            "editor_name": editor.full_name,
            "profile_url": request.build_absolute_uri(
                reverse("profile-view", kwargs={"profile_slug": person.slug})
            ),
        }

        if settings.APP_ENV in ("local", "test"):
            logger.info(NOTIFY_ABOUT_CHANGES_LOG_MESSAGE.format(**context))

            return

        notification_client = NotificationsAPIClient(settings.GOVUK_NOTIFY_API_KEY)
        notification_client.send_email_notification(
            person.email,
            settings.PROFILE_EDITED_EMAIL_TEMPLATE_ID,
            personalisation=context,
        )

    @staticmethod
    def update_groups_and_permissions(
        person: Person, is_person_admin: bool, is_team_admin: bool, is_superuser: bool
    ) -> Optional[Person]:
        """Update the groups and permissions of a given person.

        Note that this method does call save on the `person.user` instance.

        Args:
            person: The given person.
            is_person_admin: Whether the user should be a person admin.
            is_team_admin: Whether the user should be a team admin.
            is_superuser: Whether the user should be a superuser.

        Returns:
            Optional[Person]: The given person or None.
        """
        if not person.user:
            return None

        user = person.user

        person_admin_group = Group.objects.get(name=PERSON_ADMIN_GROUP_NAME)
        team_admin_group = Group.objects.get(name=TEAM_ADMIN_GROUP_NAME)

        if is_person_admin:
            user.groups.add(person_admin_group)
        else:
            user.groups.remove(person_admin_group)

        if is_team_admin:
            user.groups.add(team_admin_group)
        else:
            user.groups.remove(team_admin_group)

        user.is_superuser = is_superuser
        user.save()

        return person

    def notify_about_deletion(self, person: Person, deleted_by: User) -> None:
        if deleted_by == person.user:
            return None

        context = {
            "profile_name": person.full_name,
            "editor_name": deleted_by.get_full_name(),
        }

        if settings.APP_ENV in ("local", "test"):
            logger.info(f"{person.full_name}'s profile was deleted")

            return

        notification_client = NotificationsAPIClient(settings.GOVUK_NOTIFY_API_KEY)
        notification_client.send_email_notification(
            person.user.email,
            settings.PROFILE_DELETED_EMAIL_TEMPLATE_ID,
            personalisation=context,
        )


class PersonAuditLogSerializer(AuditLogSerializer):
    model = Person

    # I know this looks strange, but it is here to protect us from forgetting to update
    # the audit log code when we update the model. The tests will execute this code so
    # it should fail locally and in CI. If you need to update this number you can call
    # `len(Person._meta.get_fields())` in a shell to get the new value.
    assert len(Person._meta.get_fields()) == 45, (
        "It looks like you have updated the `Person` model. Please make sure you have"
        " updated `PersonAuditLogSerializer.serialize` to reflect any field changes."
    )

    def serialize(self, instance: Person) -> ObjectRepr:
        person = (
            Person.objects.get_annotated()
            .filter(pk=instance.pk)
            .values()
            .annotate(
                country_code=F("country__iso_2_code"),
                country_name=F("country__name"),
                # Note the use of `ArrayAgg` to denormalize and flatten many-to-many
                # relationships.
                workdays=ArrayAgg(
                    "workdays__name",
                    filter=Q(workdays__name__isnull=False),
                    distinct=True,
                ),
                roles=ArrayAgg(
                    Concat(
                        "roles__job_title",
                        Value(" in "),
                        "roles__team__name",
                        Case(
                            When(
                                roles__head_of_team=True, then=Value(" (head of team)")
                            ),
                            default=Value(""),
                        ),
                    ),
                    filter=Q(roles__isnull=False),
                    distinct=True,
                ),
                groups=ArrayAgg(
                    "user__groups__name",
                    filter=Q(user__groups__name__isnull=False),
                    distinct=True,
                ),
                user_permissions=ArrayAgg(
                    "user__user_permissions__name",
                    filter=Q(user__user_permissions__name__isnull=False),
                    distinct=True,
                ),
                user__username=F("user__username"),
                manager__slug=F("manager__slug"),
                manager__full_name=(
                    Concat("manager__first_name", Value(" "), "manager__last_name")
                ),
            )[0]
        )

        # Encode the slug from `UUID` to `str` before returning.
        person["slug"] = str(person["slug"])
        person["manager__slug"] = str(person["manager__slug"])

        del person["login_count"]
        del person["old_country_id"]

        return person
