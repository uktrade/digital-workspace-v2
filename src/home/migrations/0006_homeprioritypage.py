# Generated by Django 4.2.15 on 2024-08-29 15:26

from django.db import migrations, models
import django.db.models.deletion
import home.validators
import modelcluster.fields


def create_home_priority_pages(apps, schema_editor):
    HomePage = apps.get_model("home", "HomePage")
    HomePriorityPage = apps.get_model("home", "HomePriorityPage")
    HomeNewsOrder = apps.get_model("home", "HomeNewsOrder")

    home_page = HomePage.objects.first()
    hpp_count = 3
    for hno in HomeNewsOrder.objects.all().order_by("order"):
        HomePriorityPage.objects.create(
            home_page=home_page, page=hno.news_page, order=hno.order
        )
        hpp_count -= 1
        if hpp_count == 0:
            break


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailcore", "0091_remove_revision_submitted_for_moderation"),
        ("home", "0005_alter_homenewsorder_options"),
    ]

    operations = [
        migrations.CreateModel(
            name="HomePriorityPage",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("order", models.IntegerField(blank=True, editable=False, null=True)),
                (
                    "home_page",
                    modelcluster.fields.ParentalKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="priority_pages",
                        to="home.homepage",
                    ),
                ),
                (
                    "page",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to="wagtailcore.page",
                        validators=[home.validators.validate_home_priority_pages],
                    ),
                ),
            ],
            options={
                "ordering": ["order"],
                "abstract": False,
            },
        ),
        migrations.RunPython(
            create_home_priority_pages,
            reverse_code=migrations.RunPython.noop,
        ),
    ]