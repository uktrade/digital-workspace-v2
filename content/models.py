from django.db import models

from wagtail.core.models import Page
from wagtail.core.fields import RichTextField, StreamField
from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel
from wagtail.search import index

from . import blocks


class ContentIndexPage(Page):
    RICH_TEXT_FEATURES = ['bold', 'italic', 'ol', 'ul', 'link', 'document-link']

    excerpt = models.CharField(
        blank=False,
        max_length=250,
        help_text="""Short summary of what this section is about (will be
        displayed in the list of children on this page's parent page)"""
    )
    introduction = RichTextField(
        blank=True,
        features=RICH_TEXT_FEATURES,
        help_text="""Some text to describe what this section is about (will be
        displayed above the list of child pages)"""
    )

    subpage_types = ['content.ContentIndexPage', 'content.ContentPage']

    search_fields = Page.search_fields + [
        index.SearchField('excerpt'),
        index.SearchField('introduction')
    ]

    content_panels = Page.content_panels + [
        FieldPanel('excerpt'),
        FieldPanel('introduction', classname="full")
    ]

class ContentPage(Page):
    excerpt = models.CharField(max_length=250, blank=True)
    body = StreamField([
        ('heading', blocks.HeadingBlock()),
        ('text', blocks.TextBlock()),
        ('image', blocks.ImageBlock()),
        ('internal_media', blocks.InternalMediaBlock()),
        ('data_table', blocks.DataTableBlock())
    ])

    subpage_types = []

    search_fields = Page.search_fields + [
        index.SearchField('excerpt'),
        index.SearchField('body')
    ]

    content_panels = Page.content_panels + [
        FieldPanel('excerpt'),
        StreamFieldPanel('body')
    ]
