from django.db import models

from wagtail.core.models import Page
from wagtail.core.fields import RichTextField
from wagtail.admin.edit_handlers import FieldPanel
from wagtail.search import index


class ContentIndexPage(Page):
    excerpt = models.CharField(max_length=250, blank=True)
    introduction = RichTextField(blank=True)

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
    body = RichTextField(blank=True)

    subpage_types = []

    search_fields = Page.search_fields + [
        index.SearchField('excerpt'),
        index.SearchField('body')
    ]

    content_panels = Page.content_panels + [
        FieldPanel('excerpt'),
        FieldPanel('body', classname="full")
    ]
