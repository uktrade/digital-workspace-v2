# Generated by Django 5.1.8 on 2025-04-24 13:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("peoplefinder", "0126_insert_grade_ordering_data"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="person",
            options={
                "ordering": ["grade", "first_name", "last_name"],
                "permissions": [
                    ("can_view_inactive_profiles", "Can view inactive profiles")
                ],
            },
        ),
    ]
