# Generated by Django 3.2.12 on 2022-03-30 12:38

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("peoplefinder", "0078_auto_20220330_1236"),
    ]

    operations = [
        migrations.AlterField(
            model_name="person",
            name="edited_or_confirmed_at",
            field=models.DateTimeField(),
        ),
    ]
