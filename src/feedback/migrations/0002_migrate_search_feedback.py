# Generated by Django 4.1.10 on 2023-08-08 14:35

from django.db import migrations


def migrate_search_feedback(apps, schema_editor):
    Feedback = apps.get_model("django_feedback_govuk", "Feedback")
    SearchFeedbackV1 = apps.get_model("feedback", "SearchFeedbackV1")
    for feedback in Feedback.objects.all():
        search_feedback = SearchFeedbackV1.objects.create(
            submitter=feedback.submitter,
            satisfaction=feedback.satisfaction,
            comment=feedback.comment,
        )
        # Update the base feedback model with the submitted_at field to override the auto_now_add
        SearchFeedbackV1.objects.filter(pk=search_feedback.pk).update(
            submitted_at=feedback.submitted_at,
        )
        feedback.delete()


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("feedback", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(migrate_search_feedback, migrations.RunPython.noop)
    ]