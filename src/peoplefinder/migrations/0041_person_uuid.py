# Generated by Django 3.2.4 on 2021-09-01 14:01

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("peoplefinder", "0040_buildings_data"),
    ]

    operations = [
        migrations.AddField(
            model_name="person",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, editable=False, null=True),
        ),
    ]
