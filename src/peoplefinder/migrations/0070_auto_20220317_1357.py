# Generated by Django 3.2.12 on 2022-03-17 13:57

from django.db import migrations


def delete_all_people(apps, schema_editor):
    Person = apps.get_model("peoplefinder", "Person")

    Person.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("peoplefinder", "0069_auto_20220317_1357"),
    ]

    operations = [migrations.RunPython(delete_all_people)]
