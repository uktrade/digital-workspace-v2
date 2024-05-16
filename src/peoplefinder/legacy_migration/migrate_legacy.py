"""
Migrating legacy data from the old People Finder.

Here is the initial PR that added the migration code:
https://github.com/uktrade/digital-workspace-v2/pull/115

Order of table migrations:
  1. Groups -> Team
  2. People -> Person
    3. Memberships -> TeamMember (for each person)
  4. Versions -> LegacyAuditLog

Delete order is the reverse.

A person's manager can only be set once all people have been migrated.
"""

import io
import logging
from collections import deque
from functools import cache
from pathlib import Path
from typing import Callable, Optional, Union

import boto3
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils.timezone import make_aware

from peoplefinder.legacy_migration.legacy_models import (
    Groups,
    Memberships,
    People,
    Versions,
)
from peoplefinder.models import (
    AdditionalRole,
    AuditLog,
    Building,
    Country,
    Grade,
    KeySkill,
    LearningInterest,
    LegacyAuditLog,
    Network,
    Person,
    Profession,
    Team,
    TeamMember,
    Workday,
)
from peoplefinder.services.person import PersonService
from peoplefinder.services.team import TeamService
from user.models import User


BATCH_SIZE = 100

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--skip-photos", action="store_true")

    def handle(self, *args, **options):
        logger.info("Begin legacy migration!")

        LegacyAuditLog.objects.all().delete()
        logger.info("Deleted legacy audit log")
        AuditLog.objects.all().delete()
        logger.info("Deleted audit log")
        # All team members and the team tree will be deleted using cascades.
        Person.objects.all().delete()
        logger.info("Deleted people")
        Team.objects.all().delete()
        logger.info("Deleted teams")

        migrate_teams()
        logger.info("Migrated teams")
        migrate_people(**options)
        logger.info("Migrated people")
        create_audit_log()
        logger.info("Created audit log")
        migrate_legacy_audit_log()
        logger.info("Migrated legacy audit log")


def migrate_people(**options):
    count = 0

    legacy_people = People.objects.prefetch_related("groups").all()

    migrate_person = person_migrator()
    profile_photo_migrator = ProfilePhotoMigrator()

    for legacy_person in legacy_people:
        user = get_user_for_legacy_person(legacy_person)

        if user:
            person, _ = Person.objects.get_or_create(user=user)
        else:
            person = Person.objects.create(user=user)

        migrate_person(legacy_person, person)

        person.save()

        if user:
            PersonService.update_groups_and_permissions(
                person=person,
                is_person_admin=legacy_person.role_people_editor,
                is_team_admin=legacy_person.role_groups_editor,
                is_superuser=legacy_person.role_administrator,
            )

        for membership in legacy_person.roles.all():
            team = get_team_for_legacy_group(membership.group)

            TeamMember.objects.get_or_create(
                person=person,
                team=team,
                job_title=membership.role,
                head_of_team=membership.leader,
            )

        if not options["skip_photos"]:
            profile_photo_migrator.migrate(legacy_person, person)

        count += 1

        if count % 100 == 0:
            logger.info("Created 100 people")

    # Now let's assign everybody's manager.
    for legacy_person in legacy_people:
        if not legacy_person.line_manager_id:
            continue

        person = get_person_for_legacy_person(legacy_person)

        legacy_manager = People.objects.get(pk=legacy_person.line_manager_id)
        manager = get_person_for_legacy_person(legacy_manager)

        if manager:
            person.manager = manager
            person.save()

    logger.info(f"Created {count} people in total")


def person_migrator():
    countries = Country.objects.in_bulk(field_name="code")
    workdays = Workday.objects.in_bulk(field_name="code")
    grades = Grade.objects.in_bulk(field_name="code")
    key_skills = KeySkill.objects.in_bulk(field_name="code")
    learning_interests = LearningInterest.objects.in_bulk(field_name="code")
    networks = Network.objects.in_bulk(field_name="code")
    professions = Profession.objects.in_bulk(field_name="code")
    additional_roles = AdditionalRole.objects.in_bulk(field_name="code")
    buildings = Building.objects.in_bulk(field_name="code")

    def migrate_person(legacy_person, person):
        # country
        if legacy_person.country:
            person.country = countries[legacy_person.country]

        # workdays
        workdays_field_code = (
            ("works_monday", "mon"),
            ("works_tuesday", "tue"),
            ("works_wednesday", "wed"),
            ("works_thursday", "thu"),
            ("works_friday", "fri"),
            ("works_saturday", "sat"),
            ("works_sunday", "sun"),
        )
        person.workdays.set(
            [
                workdays[code]
                for field, code in workdays_field_code
                if getattr(legacy_person, field)
            ]
        )

        # grade
        if legacy_person.grade:
            person.grade = grades[legacy_person.grade]

        # key_skills
        person.key_skills.set(
            [key_skills[code] for code in legacy_person.key_skills if code]
        )

        # learning_interests
        person.learning_interests.set(
            [
                learning_interests[code]
                for code in legacy_person.learning_and_development
                if code
            ]
        )

        # networks
        person.networks.set([networks[code] for code in legacy_person.networks if code])

        # professions
        person.professions.set(
            [professions[code] for code in legacy_person.professions if code]
        )

        # additional_roles
        person.additional_roles.set(
            [
                additional_roles[code]
                for code in legacy_person.additional_responsibilities
                if code
            ]
        )

        # buildings
        new_buildings = set()

        for code in legacy_person.building:
            if not code:
                continue

            if code in ["whitehall_55", "whitehall_3", "king_charles"]:
                code = "old_admiralty"

            new_buildings.add(buildings[code])

        person.buildings.set(new_buildings)

        # legacy_slug
        if legacy_person.slug:
            person.legacy_slug = legacy_person.slug

        if legacy_person.ditsso_user_id:
            person.legacy_sso_user_id = legacy_person.ditsso_user_id

        # first name
        if legacy_person.given_name:
            person.first_name = legacy_person.given_name

        # last name
        if legacy_person.surname:
            person.last_name = legacy_person.surname

        # email
        if legacy_person.email:
            person.email = legacy_person.email

        # pronouns
        if legacy_person.pronouns:
            person.pronouns = legacy_person.pronouns

        # contact_email
        if legacy_person.contact_email:
            person.contact_email = legacy_person.contact_email

        # primary_phone_number
        if legacy_person.primary_phone_number:
            person.primary_phone_number = legacy_person.primary_phone_number

        # secondary_phone_number
        if legacy_person.secondary_phone_number:
            person.secondary_phone_number = legacy_person.secondary_phone_number

        # town_city_or_region
        if legacy_person.city:
            person.town_city_or_region = legacy_person.city

        # regional_building
        if legacy_person.other_uk:
            person.regional_building = legacy_person.other_uk

        # international_building
        if legacy_person.other_overseas:
            person.international_building = legacy_person.other_overseas

        # location_in_building
        if legacy_person.location_in_building:
            person.location_in_building = legacy_person.location_in_building

        # do_not_work_for_dit
        if legacy_person.line_manager_not_required:
            person.do_not_work_for_dit = legacy_person.line_manager_not_required

        # other_key_skills
        if legacy_person.other_key_skills:
            person.other_key_skills = legacy_person.other_key_skills

        # fluent_languages
        if legacy_person.language_fluent:
            person.fluent_languages = legacy_person.language_fluent

        # intermediate_languages
        if legacy_person.language_intermediate:
            person.intermediate_languages = legacy_person.language_intermediate

        # other_learning_interests
        if legacy_person.other_learning_and_development:
            person.other_learning_interests = (
                legacy_person.other_learning_and_development
            )

        # other_additional_roles
        if legacy_person.other_additional_responsibilities:
            if len(legacy_person.other_additional_responsibilities) > 400:
                logger.warn(
                    f"{legacy_person} other_additional_responsibilities length is > 400"
                    " and will be truncated"
                )

            person.other_additional_roles = (
                legacy_person.other_additional_responsibilities[:400]
            )

        # previous_experience
        person.previous_experience = legacy_person.previous_positions or ""

    return migrate_person


@cache
def get_user_for_legacy_person(person: People) -> Optional[User]:
    try:
        user = User.objects.get(legacy_sso_user_id=person.ditsso_user_id)
    except User.DoesNotExist:
        user = None

    return user


@cache
def get_person_for_legacy_person(legacy_person: People) -> Person:
    return Person.objects.get(legacy_slug=legacy_person.slug)


def migrate_teams():
    team_service = TeamService()

    count = 0
    queue = deque([None])

    while queue:
        ancestor = queue.popleft()

        if ancestor:
            groups = Groups.objects.filter(
                Q(ancestry=ancestor.pk) | Q(ancestry__endswith=f"/{ancestor.pk}")
            )
        else:
            groups = Groups.objects.filter(ancestry__isnull=True)

        queue.extend(groups)

        parent = get_team_for_legacy_group(ancestor) if ancestor else None

        for group in groups:
            team = Team.objects.create(
                name=group.name,
                abbreviation=group.acronym if group.acronym else None,
                slug=group.slug,
                description=group.description and group.description.strip(),
            )

            team_service.add_team(team, parent or team)

            count += 1

            if count % 100 == 0:
                logger.info("Created 100 teams")

    logger.info(f"Created {count} teams in total")


@cache
def get_team_for_legacy_group(group: Groups) -> Team:
    return Team.objects.get(
        name=group.name,
        abbreviation=group.acronym if group.acronym else None,
        slug=group.slug,
    )


class ProfilePhotoMigrator:
    def __init__(self):
        self.client = self.get_s3_client(
            access_key=settings.PFM_AWS_ACCESS_KEY_ID,
            secret_key=settings.PFM_AWS_SECRET_ACCESS_KEY,
        )
        self.bucket = settings.PFM_AWS_STORAGE_BUCKET_NAME

    def migrate(self, legacy_person, person):
        if not legacy_person.profile_photo_id:
            logger.warning(f"{legacy_person} has no photo")

            return

        if not self._get_photo_keys(legacy_person):
            logger.warning(f"{legacy_person} has no photos")

            return

        # Copy medium sized cropped photo.
        photo_key, photo_obj = self._get_photo_object(legacy_person, "medium_")
        photo_name = Path(photo_key).name.removeprefix("medium_")

        with io.BytesIO(photo_obj["Body"].read()) as photo_bytes:
            person.photo.save(photo_name, File(photo_bytes))

        # Copy small sized cropped photo.
        photo_key, photo_obj = self._get_photo_object(legacy_person, "small_")
        photo_name = Path(photo_key).name.removeprefix("small_")

        with io.BytesIO(photo_obj["Body"].read()) as photo_bytes:
            person.photo_small.save(photo_name, File(photo_bytes))

    def _get_photo_object(self, legacy_person, prefix):
        photo_keys = self._get_photo_keys(legacy_person)

        key = [x for x in photo_keys if Path(x).name.startswith(prefix)][0]

        return self._get_object(key)

    @cache  # noqa
    def _get_photo_keys(self, legacy_person):
        response = self.client.list_objects_v2(
            Bucket=self.bucket,
            Prefix=f"uploads/peoplefinder/profile_photo/image/{legacy_person.profile_photo_id}/",
        )

        if "Contents" not in response:
            return []

        return [x["Key"] for x in response["Contents"]]

    def _get_object(self, key):
        response = self.client.get_object(
            Bucket=self.bucket,
            Key=key,
        )

        return key, response

    @staticmethod
    def get_s3_client(access_key, secret_key):
        return boto3.client(
            "s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )


def create_audit_log() -> None:
    team_service = TeamService()

    for team in Team.objects.all():
        team_service.team_created(team, created_by=None)

    person_service = PersonService()

    for person in Person.objects.all():
        person_service.profile_created(person, created_by=None)


def migrate_legacy_audit_log() -> None:
    migrate = audit_log_migrator()

    objs = []
    count = 0

    for version in Versions.objects.all():
        obj = migrate(version)

        if not obj:
            continue

        objs.append(obj)

        count += 1

        if count % 100 == 0:
            LegacyAuditLog.objects.bulk_create(objs)
            objs = []
            logger.info("Created 100 audit logs")

    LegacyAuditLog.objects.bulk_create(objs)
    logger.info(f"Created {count} audit logs in total")


def audit_log_migrator() -> Callable[[Versions], Optional[LegacyAuditLog]]:
    people = People.objects.in_bulk(field_name="id")
    groups = Groups.objects.in_bulk(field_name="id")
    memberships = People.objects.in_bulk(field_name="id")

    item_type_to_lookup = {
        "Person": people,
        "Group": groups,
        "Membership": memberships,
    }

    event_to_action = {
        "create": "create",
        "update": "update",
        "destroy": "delete",
    }

    def get_related_obj(version) -> Optional[Union[People, Groups, Memberships]]:
        lookup = item_type_to_lookup[version.item_type]

        return lookup.get(version.item_id)

    def get_actor(version: Versions) -> Optional[Person]:
        if not version.whodunnit:
            return None

        try:
            legacy_person = people.get(int(version.whodunnit))
        except ValueError:
            legacy_person = None

        if not legacy_person:
            return None

        user = get_user_for_legacy_person(legacy_person)

        return user

    def migrate(version: Versions) -> Optional[LegacyAuditLog]:
        related_obj = get_related_obj(version)

        if not related_obj:
            return None

        content_obj = get_content_obj(related_obj)

        if not content_obj:
            return None

        actor = get_actor(version)

        automated = (
            version.whodunnit.startswith("Automated task")
            if version.whodunnit
            else False
        )

        return LegacyAuditLog(
            content_object=content_obj,
            actor=actor,
            automated=automated,
            action=event_to_action[version.event],
            timestamp=make_aware(version.created_at),
            object=version.object,
            object_changes=version.object_changes,
        )

    return migrate


def get_content_obj(
    related_obj: Union[People, Groups, Memberships],
) -> Optional[Union[Person, Team, TeamMember]]:
    if isinstance(related_obj, People):
        user = get_user_for_legacy_person(related_obj)

        if not user:
            return None

        return user.profile
    elif isinstance(related_obj, Groups):
        try:
            return get_team_for_legacy_group(related_obj)
        except ObjectDoesNotExist:
            return None
    elif isinstance(related_obj, Memberships):
        user = get_user_for_legacy_person(related_obj.person)

        if not user:
            return None

        try:
            team = get_team_for_legacy_group(related_obj.group)
        except ObjectDoesNotExist:
            return None

        return TeamMember.objects.get(person=user.profile, team=team)
    else:
        raise ValueError(f"Invalid related_obj {related_obj!r}")
