# Generated by Django 4.2.11 on 2024-05-31 12:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailcore", "0091_remove_revision_submitted_for_moderation"),
        ("interactions", "0002_recentpageview_count"),
    ]

    operations = [
        migrations.AlterField(
            model_name="bookmark",
            name="page",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(app_label)s_%(class)ss",
                to="wagtailcore.page",
            ),
        ),
        migrations.AlterField(
            model_name="recentpageview",
            name="page",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(app_label)s_%(class)ss",
                to="wagtailcore.page",
            ),
        ),
    ]