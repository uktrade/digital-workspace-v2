# Generated by Django 3.1.8 on 2021-06-10 10:40

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("peoplefinder", "0017_learning_interests_data"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="country",
            options={"ordering": ["name"]},
        ),
        migrations.AlterModelOptions(
            name="grade",
            options={"ordering": ["name"]},
        ),
        migrations.AlterModelOptions(
            name="keyskill",
            options={"ordering": ["name"]},
        ),
        migrations.AlterModelOptions(
            name="learninginterest",
            options={"ordering": ["name"]},
        ),
    ]
