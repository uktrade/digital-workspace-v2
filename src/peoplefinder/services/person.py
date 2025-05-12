import logging
from datetime import timedelta
from typing import Any, Dict, List, Optional, Tuple, TypedDict
from urllib.parse import urlparse, urlunparse

import requests
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Case, F, Q, Value, When
from django.db.models.functions import Concat
from django.http import HttpRequest
from django.shortcuts import reverse
from django.utils import timezone
from django.utils.html import escape, strip_tags
from django.utils.safestring import mark_safe
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
from peoplefinder.services.team import TeamService
from peoplefinder.tasks import notify_user_about_profile_changes
from peoplefinder.types import EditSections, ProfileSections
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

You can update any profile on Digital Workspace. Find out more at: https://workspace.trade.gov.uk/working-at-dbt/policies-and-guidance/using-people-finder/
"""


class ProfileCompletionField(TypedDict, total=False):
    weight: int
    edit_section: Any  # EditSections
    form_id: str
    or_fields: List[str]


class ProfileSectionMapping(TypedDict):
    edit_section: Any  # EditSections
    fields: List[Tuple[str, str]]
    empty_text: str


class PersonService:
    # List of fields that contribute to profile completion and their weights.
    PROFILE_COMPLETION_FIELDS: Dict[str, ProfileCompletionField] = {
        "first_name": {
            "weight": 0,
            "edit_section": EditSections.PERSONAL,
        },
        "last_name": {
            "weight": 0,
            "edit_section": EditSections.PERSONAL,
        },
        # "photo": {
        #     "weight": 1,
        #     "edit_section": EditSections.PERSONAL,
        #     "form_id": "photo-form-group",
        # },
        "email": {
            "weight": 1,
            "edit_section": EditSections.CONTACT,
        },
        "primary_phone_number": {
            "weight": 1,
            "edit_section": EditSections.CONTACT,
        },
        "location": {
            "weight": 1,
            "or_fields": [
                "uk_office_location",
                "international_building",
            ],
            "edit_section": EditSections.LOCATION,
            "form_id": "id_uk_office_location",
        },
        "remote_working": {
            "weight": 1,
            "edit_section": EditSections.LOCATION,
            "form_id": "id_remote_working_1",
        },
        "manager": {
            "weight": 1,
            "or_fields": [
                "manager",
                "do_not_work_for_dit",
                "international_building",
            ],
            "edit_section": EditSections.TEAMS,
            "form_id": "manager-component",
        },
        "roles": {  # Related objects
            "weight": 1,
            "edit_section": EditSections.TEAMS,
            "form_id": "team-and-role-heading",
        },
    }

    # Map of profile sections to edit sections and fields.
    PROFILE_SECTION_MAPPING: Dict[Any, ProfileSectionMapping] = {
        ProfileSections.TEAM_AND_ROLE: {
            "fields": [
                ("get_grade_display", "Grade"),
                ("get_manager_display", "Manager"),
                ("get_roles_display", "My role(s)"),
            ],
            "empty_text": "Add your grade, team, and role to your profile.",
        },
        ProfileSections.WAYS_OF_WORKING: {
            "fields": [
                ("get_remote_working_display", "Where I work"),
                ("get_office_location_display", "Office location"),
                ("usual_office_days", "Days in the office"),
                ("international_building", "International location"),
                ("get_workdays_display", "Working days"),
            ],
            "empty_text": "Add your office location and working pattern to your profile.",
        },
        ProfileSections.SKILLS: {
            "fields": [
                ("get_key_skills_display", "Skills"),
                ("fluent_languages", "Languages"),
                (
                    "get_learning_interests_display",
                    "Learning and development interests",
                ),
                ("get_networks_display", "Networks"),
                ("get_professions_display", "Professions"),
                (
                    "get_additional_roles_display",
                    "Additional roles or responsibilities",
                ),
                ("previous_experience", "Previous experience"),
            ],
            "empty_text": "Add skills, interests, and networks to your profile.",
        },
    }

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
            # Finally try and match on the first and last name.
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
            preferred_first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            contact_email=user.email,
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

            self.trigger_profile_change_notification(request, person)

        for team_id in person.roles.all().values_list("team__pk", flat=True).distinct():
            TeamService().clear_profile_completion_cache(team_id)

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

    def trigger_profile_change_notification(
        self, request: HttpRequest, person: Person
    ) -> None:
        editor = request.user.profile

        if editor == person:
            return None

        personalisation = {
            "profile_name": person.full_name,
            "editor_name": editor.full_name,
            "profile_url": request.build_absolute_uri(
                reverse("profile-view", kwargs={"profile_slug": person.slug})
            ),
        }

        if settings.APP_ENV in ("local", "test"):
            logger.info(NOTIFY_ABOUT_CHANGES_LOG_MESSAGE.format(**personalisation))

            return

        countdown = 300  # 5 minutes.
        notify_user_about_profile_changes.apply_async(
            args=(
                person.pk,
                personalisation,
                countdown,
            ),
            countdown=countdown,
        )

    def notify_about_changes_debounce(
        self, person_pk, personalisation, countdown
    ) -> None:
        """
        Don't call this method directly, use `trigger_profile_change_notification`.

        See `peoplefinder.tasks.notify_user_about_profile_changes` for more
        details.
        """
        person = Person.objects.get(pk=person_pk)

        if countdown:
            can_run_time = person.edited_or_confirmed_at + timedelta(seconds=countdown)
            if timezone.now() < can_run_time:
                # If the person model was edited more recently than the delay,
                # then don't send a notification as something has happened since
                # the task was triggered.
                return None

        notification_client = NotificationsAPIClient(settings.GOVUK_NOTIFY_API_KEY)
        notification_client.send_email_notification(
            email_address=person.email,
            template_id=settings.PROFILE_EDITED_EMAIL_TEMPLATE_ID,
            personalisation=personalisation,
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

        # Find a the most suitable email.
        email = (
            (person.user and person.user.email) or person.contact_email or person.email
        )

        # If we can't find one, return.
        if not email:
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
            email,
            settings.PROFILE_DELETED_EMAIL_TEMPLATE_ID,
            personalisation=context,
        )

    def get_profile_completion(self, person: "Person") -> int:
        """
        Profile completion is calculated by adding up the weights of the fields
        that have been completed and dividing by the total of all the weights.
        """
        complete_fields = 0
        field_statuses = self.profile_completion_field_statuses(person)
        for field_status in field_statuses:
            if field_statuses[field_status]:
                complete_fields += self.PROFILE_COMPLETION_FIELDS[field_status][
                    "weight"
                ]

        total_field_weights = sum(
            [f["weight"] for f in self.PROFILE_COMPLETION_FIELDS.values()]
        )
        percentage = (complete_fields / total_field_weights) * 100
        return int(percentage)

    def profile_completion_field_statuses(self, person: "Person") -> Dict[str, bool]:
        statuses: Dict[str, bool] = {}
        for (
            profile_completion_field,
            pcf_dict,
        ) in self.PROFILE_COMPLETION_FIELDS.items():
            if profile_completion_field == "roles":
                # If the person doesn't have a PK then there can't be any relationships.
                if not person._state.adding and person.roles.all().exists():
                    statuses[profile_completion_field] = True
                    continue

            if "or_fields" in pcf_dict:
                if any(
                    [getattr(person, or_field) for or_field in pcf_dict["or_fields"]]
                ):
                    statuses[profile_completion_field] = True
                    continue

            field_value = getattr(person, profile_completion_field, None)

            if field_value:
                statuses[profile_completion_field] = True
                continue

            statuses[profile_completion_field] = False
        return statuses

    def get_profile_completion_field(self, field_name: str) -> ProfileCompletionField:
        return self.PROFILE_COMPLETION_FIELDS[field_name]

    def get_profile_completion_field_edit_section(
        self, field_name: str
    ) -> EditSections:
        return self.get_profile_completion_field(field_name).get(
            "edit_section",
            EditSections.PERSONAL,
        )

    def get_profile_completion_field_form_id(self, field_name: str) -> str:
        return self.get_profile_completion_field(field_name).get(
            "form_id",
            "id_" + field_name,
        )

    def get_profile_section_mapping(
        self, profile_section: ProfileSections
    ) -> Dict[str, str]:
        return self.PROFILE_SECTION_MAPPING.get(profile_section, {})

    def get_profile_section_empty_text(
        self,
        profile_section: ProfileSections,
    ) -> str:
        return self.get_profile_section_mapping(profile_section)["empty_text"]

    def get_profile_section_values(
        self, person: "Person", profile_section: ProfileSections
    ) -> List[Tuple[str, str, str]]:
        profile_section_fields: List[Tuple[str, str]] = (
            self.get_profile_section_mapping(
                profile_section,
            ).get("fields", [])
        )
        values = []
        for field_name, field_label in profile_section_fields:
            field_value = getattr(person, field_name)

            if isinstance(field_value, str):
                # escaping field_value before using mark_safe -> https://docs.djangoproject.com/en/dev/releases/4.2.17/#django-4-2-17-release-notes
                field_value = escape(field_value)
                # Replace newlines with "<br>".
                field_value = mark_safe(  # noqa: S308
                    strip_tags(field_value).replace("\n", "<br>")
                )

            if callable(field_value):
                field_value = field_value()

            if field_value not in [None, ""]:
                values.append(
                    (
                        field_name,
                        field_label,
                        field_value,
                    )
                )
        return values

    @staticmethod
    def get_verified_emails(person: Person) -> list[str]:
        user_email = person.user.email  # @TODO prefer UUID if we can get it from SSO
        authbroker_url = urlparse(settings.AUTHBROKER_URL)
        url = urlunparse(authbroker_url._replace(path="/emails/"))
        params = {"email": user_email}
        headers = {"Authorization": f"bearer {settings.AUTHBROKER_INTROSPECTION_TOKEN}"}

        response = requests.get(url, params, headers=headers, timeout=5)

        if response.status_code == 200:
            resp_json = response.json()
            return resp_json["emails"]
        else:
            logger.error(
                f"Response code [{response.status_code}] from authbroker emails endpoint for {user_email}"
            )
        return []


class PersonAuditLogSerializer(AuditLogSerializer):
    model = Person

    # I know this looks strange, but it is here to protect us from forgetting to update
    # the audit log code when we update the model. The tests will execute this code so
    # it should fail locally and in CI. If you need to update this number you can call
    # `len(Person._meta.get_fields())` in a shell to get the new value.
    assert len(Person._meta.get_fields()) == 60, (
        "It looks like you have updated the `Person` model. Please make sure you have"
        " updated `PersonAuditLogSerializer.serialize` to reflect any field changes."
    )

    def serialize(self, instance: Person) -> ObjectRepr:
        person = (
            Person.objects.filter(pk=instance.pk)
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
                key_skills=ArrayAgg(
                    "key_skills__name",
                    filter=Q(key_skills__name__isnull=False),
                    distinct=True,
                ),
                learning_interests=ArrayAgg(
                    "learning_interests__name",
                    filter=Q(learning_interests__name__isnull=False),
                    distinct=True,
                ),
                networks=ArrayAgg(
                    "networks__name",
                    filter=Q(networks__name__isnull=False),
                    distinct=True,
                ),
                professions=ArrayAgg(
                    "professions__name",
                    filter=Q(professions__name__isnull=False),
                    distinct=True,
                ),
                additional_roles=ArrayAgg(
                    "additional_roles__name",
                    filter=Q(additional_roles__name__isnull=False),
                    distinct=True,
                ),
                buildings=ArrayAgg(
                    "buildings__name",
                    filter=Q(buildings__name__isnull=False),
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

        return person
