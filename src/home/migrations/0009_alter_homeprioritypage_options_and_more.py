# Generated by Django 4.2.15 on 2024-09-10 08:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0008_alter_homeprioritypage_options_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="homeprioritypage",
            options={"ordering": ["sort_order"]},
        ),
        migrations.RenameField(
            model_name="homeprioritypage",
            old_name="order",
            new_name="sort_order",
        ),
    ]
