# Generated by Django 4.2.15 on 2024-09-23 16:28

import core.models.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0002_alter_eventpage_location"),
    ]

    operations = [
        migrations.AlterField(
            model_name="eventpage",
            name="event_recording_url",
            field=core.models.fields.URLField(
                blank=True,
                help_text="Optional link to a page for others to view the recorded event.",
                null=True,
                verbose_name="View event recording link",
            ),
        ),
        migrations.AlterField(
            model_name="eventpage",
            name="offline_event_url",
            field=core.models.fields.URLField(
                blank=True,
                help_text="If the event is in person, you can add a link here for registration.",
                null=True,
                verbose_name="In person registration link",
            ),
        ),
        migrations.AlterField(
            model_name="eventpage",
            name="online_event_url",
            field=core.models.fields.URLField(
                blank=True,
                help_text="If the event is online, you can add a link here for others to join.",
                null=True,
                verbose_name="Online event link",
            ),
        ),
        migrations.AlterField(
            model_name="eventpage",
            name="submit_questions_url",
            field=core.models.fields.URLField(
                blank=True,
                help_text="Link to a page for others to submit their questions.",
                null=True,
                verbose_name="Submit questions link",
            ),
        ),
    ]