# Generated by Django 4.1.9 on 2023-07-17 09:49

from django.db import migrations


def fill_empty_excerpts(apps, schema_editor):
    ContentPage = apps.get_model("content", "ContentPage")
    for page in ContentPage.objects.filter(excerpt__isnull=True):
        page.full_clean()
        page.save()


def noop(apps, schema_editor):
    ...


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0019_rename_search_excerpt_contentpage_excerpt"),
    ]

    operations = [migrations.RunPython(fill_empty_excerpts, noop)]