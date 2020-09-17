from django.contrib.auth import get_user_model
from django.db import models
from wagtail.admin.edit_handlers import (
    FieldPanel,
    StreamFieldPanel,
    InlinePanel,
    FieldRowPanel,
)
from wagtail.core import blocks as wagtail_blocks
from wagtail.core.fields import StreamField
from wagtail.core.models import Page
from wagtail.search import index
from wagtail.snippets.models import register_snippet

from content import blocks

UserModel = get_user_model()

RICH_TEXT_FEATURES = ["bold", "italic", "ol", "ul", "link", "document-link"]


@register_snippet
class Theme(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    summary = models.CharField(max_length=255)

    def __str__(self):
        return self.title

    panels = [
        FieldPanel('title'),
        FieldPanel('summary'),
    ]


class ContentPage(Page):
    is_creatable = False
    show_in_menus = True

    legacy_guid = models.CharField(
        blank=True,
        null=True,
        max_length=255,
        help_text="""Wordpress GUID"""
    )

    legacy_content = models.TextField(
        blank=True,
        null=True,
        help_text="""Legacy content, pre-conversion"""
    )

    body = StreamField([
        ("heading2", blocks.Heading2Block()),
        ("heading3", blocks.Heading3Block()),
        ("text_section", blocks.TextBlock(
            blank=True,
            features=RICH_TEXT_FEATURES,
            help_text="""Some text to describe what this section is about (will be
            displayed above the list of child pages)"""
        )),
        ("image", blocks.ImageBlock()),
        ("internal_media", blocks.InternalMediaBlock()),
        ("data_table", blocks.DataTableBlock(
            help_text="""ONLY USE THIS FOR TABLULAR DATA, NOT FOR FORMATTING"""
        )),
    ])

    pinned_phrases = StreamField([
            (
                "pinned_keyword_or_phrase",
                blocks.PhraseBlock(required=False)
            ),
        ],
        blank=True,
    )

    excluded_phrases = StreamField([
            (
                "excluded_keyword_or_phrase",
                blocks.ExcludedPhraseBlock(required=False)
            ),
        ],
        blank=True,
    )

    #pinned_phrases = blocks.ListBlock(wagtail_blocks.CharBlock(required=False))

    subpage_types = []

    search_fields = Page.search_fields + [
        index.SearchField("body"),
    ]

    content_panels = Page.content_panels + [
        StreamFieldPanel("body"),
    ]

    promote_panels = Page.promote_panels + [
        StreamFieldPanel("pinned_phrases"),
        StreamFieldPanel("excluded_phrases"),
    ]


class PrivacyPolicyHome(ContentPage):
    is_creatable = False

    subpage_types = ["content.PrivacyPolicy", ]


class PrivacyPolicy(ContentPage):
    is_creatable = True

    subpage_types = []


class DirectChildrenMixin:
    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["children"] = []

        child_depth = self.depth + 1

        import importlib

        for subpage_type in self.subpage_types:
            parts = subpage_type.split(".")
            module = importlib.import_module(f"{parts[0]}.models")
            children = getattr(module, parts[1]).objects.filter(
                depth=child_depth
            ).order_by("title")
            context["children"].extend(children)

        return context
