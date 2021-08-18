"""
Order of table migrations:
  1. Groups -> Team
  2. People -> Person
  3. Memberships -> TeamMember
"""

import logging

from django.core.management.base import BaseCommand

from peoplefinder.legacy_models import Groups, Memberships, People


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info("People count:", People.objects.count())
        logger.info("Groups count:", Groups.objects.count())
        logger.info("Memberships count:", Memberships.objects.count())
        logger.info("TODO: Migrate legacy data ;P")
