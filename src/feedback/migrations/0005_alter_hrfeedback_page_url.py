# Generated by Django 4.2.15 on 2024-09-25 10:47

import core.models.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("feedback", "0004_hrfeedback"),
    ]

    operations = [
        migrations.AlterField(
            model_name="hrfeedback",
            name="page_url",
            field=core.models.fields.URLField(blank=True),
        ),
    ]
