# Generated by Django 3.2.12 on 2022-03-17 14:00

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("peoplefinder", "0070_auto_20220317_1357"),
    ]

    operations = [
        migrations.RenameModel("Person", "OldPerson"),
        migrations.RenameModel("NewPerson", "Person"),
    ]
