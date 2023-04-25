import json
from operator import itemgetter
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Generate a fixture of country data from the Data Workspace dataset"

    def add_arguments(self, parser):
        parser.add_argument("src", type=Path)
        # ISO 2 code, for example, "HK" or "TW".
        parser.add_argument(
            "--include-territory-codes", action="extend", nargs="+", default=[]
        )

    def handle(self, *args, **options):
        self.src: Path = options["src"]
        self.include_territory_codes: list = options["include_territory_codes"]

        with self.src.open() as f:
            # There should be a top level "data" key.
            self.src_data = json.load(f)["data"]

        fixture_data = self._generate_fixture_data()

        self.stdout.write(json.dumps(fixture_data, indent=2))

    def _generate_fixture_data(self):
        return sorted(
            (
                fixture_obj
                for obj in self.src_data
                if (fixture_obj := self._generate_fixture_obj(obj))
            ),
            key=itemgetter("pk"),
        )

    def _generate_fixture_obj(self, obj):
        if (
            obj["type"] != "Country"
            and obj["iso2_code"] not in self.include_territory_codes
        ):
            return None

        return {
            "model": "countries.Country",
            "pk": obj["reference_id"],
            "fields": {
                "name": obj["name"],
                "type": obj["type"].lower(),
                "iso_1_code": obj["iso1_code"],
                "iso_2_code": obj["iso2_code"],
                "iso_3_code": obj["iso3_code"],
                "overseas_region": obj["overseas_region_overseas_region_name"],
                "start_date": obj["start_date"],
                "end_date": obj["end_date"],
            },
        }
