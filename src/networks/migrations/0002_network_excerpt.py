# Generated by Django 3.1.6 on 2021-02-28 05:25

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("networks", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="network",
            name="excerpt",
            field=models.CharField(blank=True, max_length=700, null=True),
        ),
    ]
