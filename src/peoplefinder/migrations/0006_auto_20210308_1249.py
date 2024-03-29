# Generated by Django 3.1.6 on 2021-03-08 12:49

import django.db.models.deletion
from django.db import migrations, models

import peoplefinder.models


class Migration(migrations.Migration):
    dependencies = [
        ("peoplefinder", "0005_workday_data"),
    ]

    operations = [
        migrations.AlterField(
            model_name="person",
            name="country",
            field=models.ForeignKey(
                # default=peoplefinder.models.Country.get_default_id,
                on_delete=django.db.models.deletion.SET_DEFAULT,
                related_name="+",
                to="peoplefinder.country",
            ),
        ),
    ]
