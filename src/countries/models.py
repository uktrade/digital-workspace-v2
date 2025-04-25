from django.db import models

from core import field_models


class Country(models.Model):
    """Country model for use with the Data Workspace country dataset.

    Information about the dataset can be found here:
    https://data.trade.gov.uk/datasets/240d5034-6a83-451b-8307-5755672f881b#countries-territories-and-regions.

    The data required to populate this model can be downloaded from here:
    https://data.trade.gov.uk/datasets/240d5034-6a83-451b-8307-5755672f881b/grid.

    Use the provided `generate_countries_fixture` management command to produce a
    fixture which is compatible with this model.

    This model was built against the 5.35 version of the dataset.
    """

    class Type(models.TextChoices):
        COUNTRY = "country", "Country"
        TERRITORY = "territory", "Territory"

    reference_id = field_models.CharField(
        "Reference ID", primary_key=True, max_length=11
    )
    name = field_models.CharField(max_length=50, unique=True)
    type = field_models.CharField(max_length=9, choices=Type.choices)
    iso_1_code = field_models.CharField("ISO 1 Code", max_length=3, unique=True)
    iso_2_code = field_models.CharField("ISO 2 Code", max_length=2, unique=True)
    iso_3_code = field_models.CharField("ISO 3 Code", max_length=3, unique=True)
    overseas_region = field_models.CharField(max_length=40, null=True)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)

    def __str__(self):
        return self.name
