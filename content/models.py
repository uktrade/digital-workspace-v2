from django.db import models
from django.contrib.auth import get_user_model

from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.models import ClusterableModel

from wagtail.admin.edit_handlers import (
    FieldPanel,
    StreamFieldPanel,
    InlinePanel,
    MultiFieldPanel,
    PageChooserPanel,
)
from wagtail.images.edit_handlers import ImageChooserPanel

from wagtail.core.fields import StreamField
from wagtail.core.models import Page
from wagtail.search import index
from wagtail.snippets.edit_handlers import SnippetChooserPanel
from wagtail.snippets.models import register_snippet
from wagtail.contrib.routable_page.models import RoutablePageMixin, route

from modelcluster.fields import ParentalKey
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase, TagBase, ItemBase

from django.forms.widgets import CheckboxSelectMultiple

from content import blocks


UserModel = get_user_model()

RICH_TEXT_FEATURES = ["bold", "italic", "ol", "ul", "link", "document-link"]


@register_snippet
class Theme(models.Model):
    theme = models.CharField(max_length=255)

    def __str__(self):
        return self.theme

    panels = [
        FieldPanel('theme'),
    ]


@register_snippet
class Topic(ClusterableModel):
    name = models.CharField(max_length=255)
    intro = StreamField([
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
        ))
    ])
    themes = models.ManyToManyField(
        Theme,
    )

    def __str__(self):
        return self.name

    panels = [
        FieldPanel('name'),
        StreamFieldPanel('intro'),
        InlinePanel('topic_themes', label='Themes'),
    ]


class TopicTheme(models.Model):
    topic = ParentalKey(
        'content.Topic',
        on_delete=models.CASCADE,
        related_name='topic_themes',
    )

    theme = models.ForeignKey(
        'content.Theme',
        on_delete=models.CASCADE,
        related_name='theme_topics',
    )

    panels = [
        SnippetChooserPanel('theme'),
    ]

    class Meta:
        unique_together = ('topic', 'theme')


class ContentPage(Page):
    is_creatable = False
    show_in_menus = True

    legacy_guid = models.CharField(
        blank=True,
        max_length=255,
        help_text="""Wordpress GUID"""
    )

    legacy_content = models.TextField(
        blank=True,
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
        ))
    ])

    subpage_types = []

    search_fields = Page.search_fields + [
        index.SearchField("body"),
    ]

    content_panels = Page.content_panels + [
        StreamFieldPanel("body"),
    ]


class PageTopic(models.Model):
    page = ParentalKey(
        'content.PageWithTopics',
        on_delete=models.CASCADE,
        related_name='page_topics',
    )

    topic = models.ForeignKey(
        'content.Topic',
        on_delete=models.CASCADE,
        related_name='topic_pages',
    )

    panels = [
        SnippetChooserPanel('topic'),
    ]

    class Meta:
        unique_together = ('page', 'topic')


class PageWithTopics(ContentPage):
    content_panels = ContentPage.content_panels + [
        InlinePanel('page_topics', label='Topics'),
    ]


class PoliciesAndGuidance(Page):
    subpage_types = ["content.Guidance", "content.Policy", ]
    # model just for use in editor hierarchy


class Guidance(PageWithTopics):
    is_creatable = True

    subpage_types = ["content.Guidance"]


class Policy(PageWithTopics):
    is_creatable = True

    subpage_types = ["content.Policy"]


class ToolsHome(Page):
    is_creatable = False

    subpage_types = ["content.Tool"]


class Tool(PageWithTopics):
    is_creatable = True

    parent_page_types = ['content.ToolsHome']
    subpage_types = []  # Should not be able to create children
