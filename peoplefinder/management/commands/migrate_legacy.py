"""
Order of table migrations:
  1. Groups -> Team
  2. People -> Person
    3. Memberships -> TeamMember (for each person)

Delete order is the reverse.
"""

import logging
from collections import deque
from functools import cache
from typing import Optional

from django.core.management.base import BaseCommand
from django.db.models import Q

from peoplefinder.legacy_models import Groups, People
from peoplefinder.models import Person, Team, TeamMember
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

    for legacy_person in People.objects.prefetch_related("groups").all():
        user = get_user_for_legacy_person(legacy_person)

        if not user:
            continue

        person, created = Person.objects.get_or_create(user=user)

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

    logger.info(f"Created {count} people in total")


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
