# Generated by Django 5.1.8 on 2025-05-28 12:48

import django.db.models.deletion
import wagtail.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0060_sectorpage"),
    ]

    operations = [
        migrations.CreateModel(
            name="SectionPage",
            fields=[
                (
                    "basepage_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="content.basepage",
                    ),
                ),
                ("search_title", models.CharField(max_length=255)),
                ("search_headings", models.TextField(blank=True, null=True)),
                ("search_content", models.TextField(blank=True, null=True)),
                (
                    "body",
                    wagtail.fields.StreamField(
                        [
                            ("heading2", 0),
                            ("heading3", 1),
                            ("heading4", 2),
                            ("heading5", 3),
                            ("text_section", 4),
                            ("image", 9),
                            ("image_with_text", 13),
                            ("quote", 22),
                            ("embed_video", 24),
                            ("media", 26),
                            ("data_table", 27),
                            ("person_banner", 35),
                        ],
                        blank=True,
                        block_lookup={
                            0: ("content.blocks.Heading2Block", (), {}),
                            1: ("content.blocks.Heading3Block", (), {}),
                            2: ("content.blocks.Heading4Block", (), {}),
                            3: ("content.blocks.Heading5Block", (), {}),
                            4: (
                                "content.blocks.TextBlock",
                                (),
                                {
                                    "blank": True,
                                    "help_text": "Some text to describe what this section is about (will be displayed above the list of child pages)",
                                },
                            ),
                            5: ("wagtail.images.blocks.ImageChooserBlock", (), {}),
                            6: (
                                "wagtail.blocks.BooleanBlock",
                                (),
                                {
                                    "help_text": "\n        Tick if this image is entirely decorative and does not include\n        important content. This will hide the image from users using\n        screen readers.\n        ",
                                    "label": "Is this a decorative image?",
                                    "required": False,
                                },
                            ),
                            7: (
                                "wagtail.blocks.CharBlock",
                                (),
                                {
                                    "help_text": "\n        Read out by screen readers or displayed if an image does not load\n        or if images have been switched off.\n\n        Unless this is a decorative image, it MUST have alt text that\n        tells people what information the image provides, describes its\n        content and function, and is specific, meaningful and concise.\n        ",
                                    "label": "Alt text",
                                    "required": False,
                                },
                            ),
                            8: (
                                "wagtail.blocks.CharBlock",
                                (),
                                {
                                    "help_text": "\n        Optional text displayed under the image on the page to provide\n        context.\n        ",
                                    "required": False,
                                },
                            ),
                            9: (
                                "wagtail.blocks.StructBlock",
                                [
                                    [
                                        ("image", 5),
                                        ("isdecorative", 6),
                                        ("alt", 7),
                                        ("caption", 8),
                                    ]
                                ],
                                {},
                            ),
                            10: ("content.blocks.TextBlock", (), {}),
                            11: (
                                "wagtail.blocks.ChoiceBlock",
                                [],
                                {
                                    "choices": [("left", "Left"), ("right", "Right")],
                                    "help_text": "Position of the image relative to the text",
                                },
                            ),
                            12: (
                                "wagtail.blocks.CharBlock",
                                (),
                                {
                                    "help_text": "\n        Optional text displayed under the image to provide context.\n        ",
                                    "required": False,
                                },
                            ),
                            13: (
                                "wagtail.blocks.StructBlock",
                                [
                                    [
                                        ("heading", 1),
                                        ("text", 10),
                                        ("image_position", 11),
                                        ("image", 5),
                                        ("image_description", 12),
                                        ("image_alt", 7),
                                    ]
                                ],
                                {},
                            ),
                            14: (
                                "wagtail.blocks.CharBlock",
                                (),
                                {"help_text": "Enter quote text"},
                            ),
                            15: (
                                "wagtail.blocks.ChoiceBlock",
                                [],
                                {
                                    "choices": [
                                        ("light", "Light grey"),
                                        ("dark", "Dark blue"),
                                    ],
                                    "label": "Choose background colour",
                                },
                            ),
                            16: (
                                "peoplefinder.blocks.PersonChooserBlock",
                                (),
                                {
                                    "help_text": "If the quote source is a DBT person, use the 'Choose a person' option and leave all other fields blank (including the 'Source image' option). If they are external to DBT, enter the person's details manually. Add an image, if you have one.",
                                    "label": "Quote source",
                                    "required": False,
                                },
                            ),
                            17: (
                                "wagtail.blocks.CharBlock",
                                (),
                                {
                                    "help_text": "Choose the person's job role. If you do not want to show a job role, choose 'Hide role'.",
                                    "label": "Source role",
                                    "required": False,
                                },
                            ),
                            18: (
                                "wagtail.blocks.CharBlock",
                                (),
                                {"label": "Quote source name", "required": False},
                            ),
                            19: (
                                "wagtail.blocks.CharBlock",
                                (),
                                {"label": "Quote source role", "required": False},
                            ),
                            20: (
                                "wagtail.blocks.CharBlock",
                                (),
                                {"label": "Quote source team", "required": False},
                            ),
                            21: (
                                "wagtail.images.blocks.ImageChooserBlock",
                                (),
                                {
                                    "help_text": "This image should be square",
                                    "label": "Quote source image",
                                    "required": False,
                                },
                            ),
                            22: (
                                "wagtail.blocks.StructBlock",
                                [
                                    [
                                        ("quote", 14),
                                        ("quote_theme", 15),
                                        ("source", 16),
                                        ("source_role_id", 17),
                                        ("source_name", 18),
                                        ("source_role", 19),
                                        ("source_team", 20),
                                        ("source_image", 21),
                                        ("source_image_alt_text", 7),
                                    ]
                                ],
                                {},
                            ),
                            23: (
                                "wagtail.embeds.blocks.EmbedBlock",
                                (),
                                {
                                    "help_text": "Paste a URL from Microsoft Stream or Youtube. Please use the page URL rather than the URL from the embed code."
                                },
                            ),
                            24: (
                                "wagtail.blocks.StructBlock",
                                [[("video", 23)]],
                                {"help_text": "Embed a video"},
                            ),
                            25: ("content.blocks.MediaChooserBlock", (), {}),
                            26: (
                                "wagtail.blocks.StructBlock",
                                [[("media_file", 25)]],
                                {"help_text": "Link to a media block"},
                            ),
                            27: (
                                "content.blocks.DataTableBlock",
                                (),
                                {
                                    "help_text": "ONLY USE THIS FOR TABLULAR DATA, NOT FOR FORMATTING"
                                },
                            ),
                            28: (
                                "peoplefinder.blocks.PersonChooserBlock",
                                (),
                                {"required": False},
                            ),
                            29: (
                                "wagtail.blocks.CharBlock",
                                (),
                                {
                                    "help_text": "Choose the person's job role. If you do not want to show a job role, choose 'Hide role'.",
                                    "label": "Person role",
                                    "required": False,
                                },
                            ),
                            30: ("wagtail.blocks.CharBlock", (), {"required": False}),
                            31: (
                                "wagtail.images.blocks.ImageChooserBlock",
                                (),
                                {
                                    "help_text": "This image should be square.",
                                    "required": False,
                                },
                            ),
                            32: (
                                "wagtail.blocks.CharBlock",
                                (),
                                {
                                    "help_text": "\n        Read out by screen readers or displayed if an image does not load\n        or if images have been switched off.\n\n        Unless this is a decorative image, it MUST have alt text that\n        tells people what information the image provides, describes its\n        content and function, and is specific, meaningful and concise.\n        ",
                                    "label": "Alt text for person image",
                                    "required": False,
                                },
                            ),
                            33: (
                                "wagtail.images.blocks.ImageChooserBlock",
                                (),
                                {
                                    "label": "Secondary image (decorative)",
                                    "required": False,
                                },
                            ),
                            34: (
                                "wagtail.blocks.CharBlock",
                                (),
                                {
                                    "help_text": "\n        Read out by screen readers or displayed if an image does not load\n        or if images have been switched off.\n\n        Unless this is a decorative image, it MUST have alt text that\n        tells people what information the image provides, describes its\n        content and function, and is specific, meaningful and concise.\n        ",
                                    "label": "Alt text for secondary image",
                                    "required": False,
                                },
                            ),
                            35: (
                                "wagtail.blocks.StructBlock",
                                [
                                    [
                                        ("person", 28),
                                        ("person_role_id", 29),
                                        ("person_name", 30),
                                        ("person_role", 30),
                                        ("person_image", 31),
                                        ("person_image_alt_text", 32),
                                        ("secondary_image", 33),
                                        ("secondary_image_alt_text", 34),
                                    ]
                                ],
                                {},
                            ),
                        },
                        null=True,
                    ),
                ),
                (
                    "sections",
                    wagtail.fields.StreamField(
                        [("dw_section_card", 6)],
                        blank=True,
                        block_lookup={
                            0: (
                                "content.blocks.HeadingBlock",
                                (),
                                {"max_length": 30, "required": False},
                            ),
                            1: ("wagtail.blocks.PageChooserBlock", (), {}),
                            2: (
                                "content.blocks.HeadingBlock",
                                (),
                                {
                                    "help_text": "By default, the name of the page will be the title. Override it using the below field.",
                                    "max_length": 30,
                                    "required": False,
                                },
                            ),
                            3: (
                                "wagtail.blocks.CharBlock",
                                (),
                                {"max_length": 70, "required": False},
                            ),
                            4: (
                                "wagtail.blocks.StructBlock",
                                [[("page", 1), ("title", 2), ("summary", 3)]],
                                {},
                            ),
                            5: (
                                "wagtail.blocks.StreamBlock",
                                [[("dw_navigation_card", 4)]],
                                {"label": "Section Elements", "required": True},
                            ),
                            6: (
                                "wagtail.blocks.StructBlock",
                                [[("section_title", 0), ("section_elements", 5)]],
                                {},
                            ),
                        },
                    ),
                ),
                (
                    "useful_links",
                    wagtail.fields.StreamField(
                        [("dw_curated_page_links", 3)],
                        blank=True,
                        block_lookup={
                            0: (
                                "wagtail.blocks.CharBlock",
                                (),
                                {"help_text": "This will be displayed on the sidebar."},
                            ),
                            1: (
                                "wagtail.blocks.PageChooserBlock",
                                (),
                                {"required": False},
                            ),
                            2: ("wagtail.blocks.URLBlock", (), {"required": False}),
                            3: (
                                "wagtail.blocks.StructBlock",
                                [[("title", 0), ("page", 1), ("url", 2)]],
                                {},
                            ),
                        },
                    ),
                ),
                (
                    "pinned_phrases",
                    models.CharField(
                        blank=True,
                        help_text="A comma separated list of pinned keywords and phrases. Do not use quotes for phrases. The page will be pinned to the first page of search results for these terms.",
                        max_length=1000,
                        null=True,
                    ),
                ),
                (
                    "excluded_phrases",
                    models.CharField(
                        blank=True,
                        help_text="A comma separated list of excluded keywords and phrases. Do not use quotes for phrases. The page will be removed from search results for these terms",
                        max_length=1000,
                        null=True,
                    ),
                ),
                (
                    "excerpt",
                    models.CharField(
                        blank=True,
                        help_text="A summary of the page to be shown in search results. (making this field empty will result in an autogenerated excerpt)",
                        max_length=700,
                        null=True,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("content.basepage", models.Model),
        ),
        migrations.DeleteModel(
            name="SectorPage",
        ),
    ]
