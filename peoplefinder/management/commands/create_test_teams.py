from django.core.management.base import BaseCommand

from peoplefinder.models import Team
from peoplefinder.services.team import TeamService

TREE_HELP = """Team tree:
.
└── SpaceX
    ├── Astronauts
    ├── Engineering
    │   └── Software
    ├── Human Resources
    └── Catering
        └── Bakery
"""


class Command(BaseCommand):
    help = """Create teams for local testing purposes"""

    def handle(self, *args, **options):
        team_service = TeamService()

        # SpaceX
        spacex, spacex_created = Team.objects.get_or_create(
            name="SpaceX", slug="spacex"
        )
        astronauts, astronauts_created = Team.objects.get_or_create(
            name="Astronauts", slug="astronauts"
        )
        engineering, engineering_created = Team.objects.get_or_create(
            name="Engineering", slug="engineering"
        )
        software, software_created = Team.objects.get_or_create(
            name="Software", slug="software"
        )
        hr, hr_created = Team.objects.get_or_create(
            name="Human Resources", abbreviation="HR", slug="human-resources"
        )
        catering, catering_created = Team.objects.get_or_create(
            name="Catering", slug="catering"
        )
        bakery, bakery_created = Team.objects.get_or_create(
            name="Bakery", slug="bakery"
        )

        if spacex_created:
            team_service.add_team(spacex, spacex)

        if astronauts_created:
            team_service.add_team(astronauts, spacex)

        if engineering_created:
            team_service.add_team(engineering, spacex)

        if software_created:
            team_service.add_team(software, engineering)

        if hr_created:
            team_service.add_team(hr, spacex)

        if catering_created:
            team_service.add_team(catering, spacex)

        if bakery_created:
            team_service.add_team(bakery, catering)

        self.stdout.write(self.style.SUCCESS("Job completed successfully"))
        self.stdout.write(self.style.SUCCESS(TREE_HELP))
