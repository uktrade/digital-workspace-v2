# Generated by Django 4.2.11 on 2024-05-28 08:53

from django.db import migrations
import wagtail.blocks
import wagtail.fields


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0037_alter_navigationpage_primary_elements_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="navigationpage",
            name="primary_elements",
            field=wagtail.fields.StreamField(
                [
                    (
                        "dw_navigation_card",
                        wagtail.blocks.StructBlock(
                            [
                                ("page", wagtail.blocks.PageChooserBlock()),
                                (
                                    "title",
                                    wagtail.blocks.CharBlock(
                                        help_text="By default, the name of the page will be the title. Override it using the below field.",
                                        max_length=30,
                                        required=False,
                                    ),
                                ),
                                (
                                    "summary",
                                    wagtail.blocks.CharBlock(
                                        max_length=70, required=False
                                    ),
                                ),
                            ]
                        ),
                    )
                ],
                blank=True,
            ),
        ),
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
                                        max_length=30,
                                        search_index=False,
                                    ),
                                ),
                                (
                                    "description",
                                    wagtail.blocks.CharBlock(
                                        max_length=70, required=False
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
                                        max_length=30, required=True
                                    ),
                                ),
                                (
                                    "description",
                                    wagtail.blocks.CharBlock(
                                        max_length=70, required=False
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
                    (
                        "dw_engagement_card",
                        wagtail.blocks.StructBlock(
                            [
                                (
                                    "page",
                                    wagtail.blocks.PageChooserBlock(
                                        page_type=["content.ContentPage"]
                                    ),
                                )
                            ]
                        ),
                    ),
                    (
                        "dw_navigation_card",
                        wagtail.blocks.StructBlock(
                            [
                                ("page", wagtail.blocks.PageChooserBlock()),
                                (
                                    "title",
                                    wagtail.blocks.CharBlock(
                                        help_text="By default, the name of the page will be the title. Override it using the below field.",
                                        max_length=30,
                                        required=False,
                                    ),
                                ),
                                (
                                    "summary",
                                    wagtail.blocks.CharBlock(
                                        max_length=70, required=False
                                    ),
                                ),
                            ]
                        ),
                    ),
                ],
                blank=True,
            ),
        ),
    ]
