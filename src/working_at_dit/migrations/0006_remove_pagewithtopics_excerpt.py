# Generated by Django 4.1.9 on 2023-06-07 12:15

from django.db import migrations


def copy_excerpts_to_parent(apps, schema_editor):
    PageWithTopics = apps.get_model("working_at_dit", "PageWithTopics")
    for pwt in PageWithTopics.objects.filter(excerpt__isnull=False):
        pwt.search_excerpt = pwt.excerpt
        pwt.save()


def copy_excerpts_from_parent(apps, schema_editor):
    PageWithTopics = apps.get_model("working_at_dit", "PageWithTopics")
    for pwt in PageWithTopics.objects.all():
        pwt.excerpt = pwt.search_excerpt
        pwt.save()


class Migration(migrations.Migration):
    dependencies = [
        ("working_at_dit", "0005_rebrand_to_dbt"),
        ("content", "0018_remove_contentpage_body_no_html_and_more"),
    ]

    operations = [
        migrations.RunPython(copy_excerpts_to_parent, copy_excerpts_from_parent),
        migrations.RemoveField(
            model_name="pagewithtopics",
            name="excerpt",
        ),
    ]
