# Generated by Django 4.2.11 on 2024-05-20 09:31

from django.db import migrations
import wagtail.blocks
import wagtail.fields


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0032_alter_navigationpage_secondary_elements"),
    ]

    operations = [
        migrations.AlterField(
            model_name="navigationpage",
            name="secondary_elements",
            field=wagtail.fields.StreamField(
                [
                    (
                        "dw_curated_page_links",
                        wagtail.blocks.StructBlock(
                            [
                                (
                                    "title",
                                    wagtail.blocks.CharBlock(
                                        form_classname="full title",
                                        icon="title",
                                        label="Title",
                                        max_length=40,
                                        search_index=False,
                                    ),
                                ),
                                (
                                    "description",
                                    wagtail.blocks.CharBlock(
                                        max_length=40, required=False
                                    ),
                                ),
                                (
                                    "pages",
                                    wagtail.blocks.ListBlock(
                                        wagtail.blocks.PageChooserBlock(label="Page"),
                                        search_index=False,
                                    ),
                                ),
                            ]
                        ),
                    ),
                    (
                        "dw_cta",
                        wagtail.blocks.StructBlock(
                            [
                                (
                                    "title",
                                    wagtail.blocks.CharBlock(
                                        max_length=80, required=True
                                    ),
                                ),
                                (
                                    "description",
                                    wagtail.blocks.CharBlock(
                                        max_length=80, required=False
                                    ),
                                ),
                                (
                                    "page",
                                    wagtail.blocks.PageChooserBlock(required=False),
                                ),
                                ("url", wagtail.blocks.URLBlock(required=False)),
                            ]
                        ),
                    ),
                ],
                blank=True,
            ),
        ),
    ]