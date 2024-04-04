from django.core.management.base import BaseCommand

from peoplefinder.models import Team
from peoplefinder.services.team import TeamService


TREE_HELP = """Team tree:
.
└── SpaceX
    ├── Astronauts
    ├── Engineering
    │   └── Software
    │       └── Backend
    │           └── Lead developer and technical architect
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
        backend, backend_created = Team.objects.get_or_create(
            name="Backend", slug="backend"
        )
        lead_dev, lead_dev_created = Team.objects.get_or_create(
            name="Lead developer and technical architect", slug="lead-dev"
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
            team_service.team_created(spacex, created_by=None)

        if astronauts_created:
            team_service.add_team(astronauts, spacex)
            team_service.team_created(astronauts, created_by=None)

        if engineering_created:
            team_service.add_team(engineering, spacex)
            team_service.team_created(engineering, created_by=None)

        if software_created:
            team_service.add_team(software, engineering)
            team_service.team_created(software, created_by=None)

        if backend_created:
            team_service.add_team(backend, software)
            team_service.team_created(backend, created_by=None)

        if lead_dev_created:
            team_service.add_team(lead_dev, backend)
            team_service.team_created(lead_dev, created_by=None)

        if hr_created:
            team_service.add_team(hr, spacex)
            team_service.team_created(hr, created_by=None)

        if catering_created:
            team_service.add_team(catering, spacex)
            team_service.team_created(catering, created_by=None)

        if bakery_created:
            team_service.add_team(bakery, catering)
            team_service.team_created(bakery, created_by=None)

        self.stdout.write(self.style.SUCCESS("Job completed successfully"))
        self.stdout.write(self.style.SUCCESS(TREE_HELP))
