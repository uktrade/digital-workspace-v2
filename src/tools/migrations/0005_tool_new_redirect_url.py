# Generated by Django 4.2.15 on 2024-09-24 13:52

import core.models.fields
from django.db import migrations


def copy_tool_pages(apps, schema_editor):
    ToolPage = apps.get_model("tools", "Tool")

    for tool_page in ToolPage.objects.all():
        tool_page.new_redirect_url = tool_page.redirect_url
        tool_page.save()


def reverse_copy_tool_pages(apps, schema_editor):
    ToolPage = apps.get_model("tools", "Tool")

    for tool_page in ToolPage.objects.all():
        tool_page.redirect_url = tool_page.new_redirect_url
        tool_page.save()


class Migration(migrations.Migration):

    dependencies = [
        ("tools", "0004_iraptooldata_iraptooldataimport_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="tool",
            name="new_redirect_url",
            field=core.models.fields.URLField(blank=True, null=True),
        ),
        migrations.RunPython(
            copy_tool_pages,
            reverse_code=reverse_copy_tool_pages,
        ),
        migrations.RemoveField(
            model_name="tool",
            name="redirect_url",
        ),
        migrations.RenameField(
            model_name="tool",
            old_name="new_redirect_url",
            new_name="redirect_url",
        ),
    ]