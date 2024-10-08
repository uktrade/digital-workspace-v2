# Generated by Django 4.2.15 on 2024-10-02 12:42

import datetime
from django.db import migrations, models
from datetime import datetime as dt
import django.utils.timezone


def copy_events(apps, schema_editor):
    EventPage = apps.get_model("events", "EventPage")

    for event_page in EventPage.objects.all():
        event_page.event_start = dt.combine(
            event_page.event_date, event_page.start_time
        )
        event_page.event_end = dt.combine(event_page.event_date, event_page.end_time)
        event_page.save()


def reverse_copy_events(apps, schema_editor):
    EventPage = apps.get_model("events", "EventPage")

    for event_page in EventPage.objects.all():
        event_page.event_date = event_page.event_start.date()
        event_page.start_time = event_page.event_start.time()
        event_page.end_time = event_page.event_end.time()
        event_page.save()


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0003_alter_eventpage_event_recording_url_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="eventpage",
            name="event_start",
            field=models.DateTimeField(
                default=django.utils.timezone.now,
                help_text="Start date/time of the event.",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="eventpage",
            name="event_end",
            field=models.DateTimeField(
                default=datetime.datetime(
                    2024, 10, 2, 12, 42, 15, 793134, tzinfo=datetime.timezone.utc
                ),
                help_text="End date/time of the event.",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="eventpage",
            name="event_date",
            field=models.DateField(
                help_text="Date and time should be entered based on the time in London/England.",
                blank=True,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="eventpage",
            name="start_time",
            field=models.TimeField(
                blank=True,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="eventpage",
            name="end_time",
            field=models.TimeField(
                blank=True,
                null=True,
            ),
        ),
        migrations.RunPython(copy_events, reverse_code=reverse_copy_events),
        migrations.RemoveField(
            model_name="eventpage",
            name="event_date",
        ),
        migrations.RemoveField(
            model_name="eventpage",
            name="start_time",
        ),
        migrations.RemoveField(
            model_name="eventpage",
            name="end_time",
        ),
    ]
