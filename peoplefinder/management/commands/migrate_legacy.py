"""
Order of table migrations:
  1. Groups -> Team
  2. People -> Person
    3. Memberships -> TeamMember (for each person)

Delete order is the reverse.

A person's manager can only be set once all people have been migrated.
"""

import logging
from collections import deque
from functools import cache
from typing import Optional

from django.core.management.base import BaseCommand
from django.db.models import Q

from peoplefinder.legacy_models import Groups, People
from peoplefinder.models import (
    AdditionalRole,
    Building,
    Country,
    Grade,
    KeySkill,
    LearningInterest,
    Network,
    Person,
    Profession,
    Team,
    TeamMember,
    Workday,
)
from peoplefinder.services.team import TeamService
from user.models import User


BATCH_SIZE = 100

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info("Begin legacy migration!")

        # All team members and the team tree will be deleted using cascades.
        Person.objects.all().delete()
        logger.info("Deleted people")
        Team.objects.all().delete()
        logger.info("Deleted teams")

        migrate_teams()
        logger.info("Migrated teams")
        migrate_people()
        logger.info("Migrated people")


def migrate_people():
    count = 0

    legacy_people = People.objects.prefetch_related("groups").all()

    migrate_person = person_migrator()

    for legacy_person in legacy_people:
        user = get_user_for_legacy_person(legacy_person)

        if not user:
            continue

        person, created = Person.objects.get_or_create(user=user)

        migrate_person(legacy_person, person)

        person.save()

        for membership in legacy_person.roles.all():
            team = get_team_for_legacy_group(membership.group)

            TeamMember.objects.create(
                person=person,
                team=team,
                job_title=membership.role,
                head_of_team=membership.leader,
            )

        count += 1

        if count % 100 == 0:
            logger.info("Created 100 people")

    # Now let's assign everybody's manager.
    for legacy_person in legacy_people:
        if not legacy_person.line_manager_id:
            continue

        user = get_user_for_legacy_person(legacy_person)

        if not user:
            continue

        manager = get_user_for_legacy_person(
            People.objects.get(pk=legacy_person.line_manager_id)
        )

        if manager:
            user.profile.manager = manager.profile
            user.profile.save()

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
        person.networks.set(
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
            person.other_additional_roles = (
                legacy_person.other_additional_responsibilities
            )

        # previous_experience
        if legacy_person.previous_positions:
            person.previous_experience = legacy_person.previous_positions

        # TODO: (PFM-165) Migrate photos.

    return migrate_person


@cache
def get_user_for_legacy_person(person: People) -> Optional[User]:
    try:
        user = User.objects.get(legacy_sso_user_id=person.ditsso_user_id)
    except User.DoesNotExist:
        user = None

    return user


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
                abbreviation=group.acronym,
                slug=group.slug,
                description=group.description,
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
        abbreviation=group.acronym,
        slug=group.slug,
    )
