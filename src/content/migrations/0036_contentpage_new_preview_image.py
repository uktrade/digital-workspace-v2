# Generated by Django 4.2.11 on 2024-05-21 10:12

from django.db import migrations, models
import django.db.models.deletion


def copy_preview_images(apps, schema_editor):
    NewsPage = apps.get_model("news", "NewsPage")

    for news_page in NewsPage.objects.all():
        news_page.new_preview_image = news_page.preview_image
        news_page.save()


def reverse_copy_preview_images(apps, schema_editor):
    NewsPage = apps.get_model("news", "NewsPage")

    for news_page in NewsPage.objects.all():
        news_page.preview_image = news_page.new_preview_image
        news_page.save()


class Migration(migrations.Migration):

    dependencies = [
        ("wagtailimages", "0025_alter_image_file_alter_rendition_file"),
        ("content", "0035_alter_navigationpage_secondary_elements"),
        ("news", "0013_auto_20230209_1441"),
    ]

    operations = [
        migrations.AddField(
            model_name="contentpage",
            name="new_preview_image",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="wagtailimages.image",
            ),
        ),
        migrations.RunPython(
            copy_preview_images,
            reverse_code=reverse_copy_preview_images,
        ),
        migrations.RenameField(
            model_name="contentpage",
            old_name="new_preview_image",
            new_name="preview_image",
        ),
    ]
