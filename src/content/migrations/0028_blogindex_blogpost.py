# Generated by Django 4.2.11 on 2024-05-15 13:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("peoplefinder", "0121_merge_20240430_0948"),
        ("content", "0026_alter_contentpage_body"),
    ]

    operations = [
        migrations.CreateModel(
            name="BlogIndex",
            fields=[
                (
                    "basepage_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="content.basepage",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("content.basepage",),
        ),
        migrations.CreateModel(
            name="BlogPost",
            fields=[
                (
                    "contentpage_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="content.contentpage",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("content.contentpage", models.Model),
        ),
    ]