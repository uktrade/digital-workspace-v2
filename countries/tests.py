import json
from io import StringIO
from pathlib import Path

from django.core.management import call_command


TEST_JSON = """
{
  "data": [
    {
      "reference_id": "ZZZZZZ00001",
      "name": "Country 1",
      "type": "Territory",
      "iso1_code": "",
      "iso2_code": "",
      "iso3_code": "",
      "overseas_region_overseas_region_name": "Somewhere",
      "start_date": null,
      "end_date": null,
      "region": "Somewhere"
    },
    {
      "reference_id": "ZZZZZZ00002",
      "name": "Country 2",
      "type": "Country",
      "iso1_code": "00Z",
      "iso2_code": "ZZ",
      "iso3_code": "ZZZ",
      "overseas_region_overseas_region_name": "Somewhere Else",
      "start_date": "1990-01-01",
      "end_date": "2022-01-01",
      "region": "Somewhere Else"
    },
    {
      "reference_id": "ZZZZZZ00003",
      "name": "Country 3",
      "type": "Territory",
      "iso1_code": "",
      "iso2_code": "AA",
      "iso3_code": "",
      "overseas_region_overseas_region_name": "Somewhere Over There",
      "start_date": null,
      "end_date": null,
      "region": "Somewhere Over There"
    }
  ]
}
"""


def test_generate_fixture_data(tmp_path: Path):
    countries_file = tmp_path / "countries.json"
    countries_file.write_text(TEST_JSON)

    out = StringIO()

    call_command(
        "generate_countries_fixture",
        str(countries_file),
        include_territory_codes=["AA"],
        stdout=out,
    )

    fixture_data = json.loads(out.getvalue())

    assert fixture_data == [
        {
            "model": "countries.Country",
            "pk": "ZZZZZZ00002",
            "fields": {
                "name": "Country 2",
                "type": "country",
                "iso_1_code": "00Z",
                "iso_2_code": "ZZ",
                "iso_3_code": "ZZZ",
                "overseas_region": "Somewhere Else",
                "start_date": "1990-01-01",
                "end_date": "2022-01-01",
            },
        },
        {
            "model": "countries.Country",
            "pk": "ZZZZZZ00003",
            "fields": {
                "name": "Country 3",
                "type": "territory",
                "iso_1_code": "",
                "iso_2_code": "AA",
                "iso_3_code": "",
                "overseas_region": "Somewhere Over There",
                "start_date": None,
                "end_date": None,
            },
        },
    ]
