# Generated by Django 3.1.6 on 2021-02-17 13:43

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("working_at_dit", "0003_howdoi_include_link_on_homepage"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pagewithtopics",
            name="excerpt",
            field=models.CharField(blank=True, max_length=700, null=True),
        ),
    ]
