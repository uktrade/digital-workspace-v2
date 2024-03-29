# Generated by Django 4.1.10 on 2023-07-12 15:32

from django.db import migrations
from django.db.models import Count


def update_uk_office_location(apps, schema_editor):
    Person = apps.get_model("peoplefinder", "Person")
    Building = apps.get_model("peoplefinder", "Building")
    UkStaffLocation = apps.get_model("peoplefinder", "UkStaffLocation")

    horse_guards_building = Building.objects.get(code="horse_guards")
    old_admiralty_building = Building.objects.get(code="old_admiralty")

    try:
        horse_guards_location = UkStaffLocation.objects.get(
            name="1 Horse Guards Road, London"
        )
        old_admiralty_building_location = UkStaffLocation.objects.get(
            name="Old Admiralty Building, London"
        )
    except UkStaffLocation.DoesNotExist:
        return None

    # Only update profiles that haven't set the uk_office_location field
    people_with_no_office_location = Person.objects.filter(
        uk_office_location__isnull=True
    )

    # Update the uk_office_location field for people that are in one building
    # and NOT the other.
    people_with_no_office_location.filter(
        buildings=horse_guards_building,
    ).exclude(
        buildings=old_admiralty_building,
    ).update(
        uk_office_location=horse_guards_location,
    )
    people_with_no_office_location.filter(
        buildings=old_admiralty_building,
    ).exclude(
        buildings=horse_guards_building,
    ).update(
        uk_office_location=old_admiralty_building_location,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("peoplefinder", "0104_ukstafflocation_person_remote_working_and_more"),
    ]

    operations = [
        migrations.RunPython(
            code=update_uk_office_location,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
