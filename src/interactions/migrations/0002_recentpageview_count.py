# Generated by Django 4.2.11 on 2024-05-31 12:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("interactions", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="recentpageview",
            name="count",
            field=models.PositiveIntegerField(default=1),
        ),
    ]
