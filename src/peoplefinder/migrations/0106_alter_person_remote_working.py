# Generated by Django 4.1.10 on 2023-07-26 13:52

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("peoplefinder", "0105_ukstafflocation_data_migration"),
    ]

    operations = [
        migrations.AlterField(
            model_name="person",
            name="remote_working",
            field=models.CharField(
                blank=True,
                choices=[
                    ("office_worker", "I work primarily from the office"),
                    ("remote_worker", "I work primarily from home (remote worker)"),
                    ("split", "I split my time between home and the office"),
                ],
                max_length=80,
                null=True,
                verbose_name="Where do you usually work?",
            ),
        ),
    ]
