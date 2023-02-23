import random

from django.core.management.base import BaseCommand
from faker import Faker

from peoplefinder.models import Person, Team


fake = Faker()


class Command(BaseCommand):
    help = "Command template"

    def add_arguments(self, parser):
        ...
        # parser.add_argument("answer", type=int)

    def handle(self, *args, **options):
        team_pks = Team.objects.values_list("pk", flat=True)

        for person in Person.objects.all():
            person.roles.all().delete()
            person.roles.create(
                team_id=random.choice(team_pks),
                job_title=fake.job(),
            )
