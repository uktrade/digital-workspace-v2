# Generated by Django 5.1.8 on 2025-04-23 11:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("peoplefinder", "0124_update_profile_completion"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="grade",
            options={"ordering": ["-ordering"]},
        ),
        migrations.AddField(
            model_name="grade",
            name="ordering",
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
