# Generated by Django 5.1.7 on 2025-03-27 16:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("networks", "0009_alter_network_network_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="network",
            name="network_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("dbt_initiatives", "DBT initiatives"),
                    ("department_function", "Department/function"),
                    ("diversity_and_inclusion", "Diversity and inclusion"),
                    ("health_and_wellbeing", "Health and wellbeing"),
                    ("interests_and_hobbies", "Interests and hobbies"),
                    (
                        "professional_networks_and_skills",
                        "Professional networks and skills",
                    ),
                    ("social_and_sports", "Social and sports"),
                    ("volunteering", "Volunteering"),
                ],
                max_length=50,
                null=True,
            ),
        ),
    ]
