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


from content.models import ContentPage


class WorkingAtDITHome(ContentPage):
    panels = [
        FieldPanel('name'),
        StreamFieldPanel('body'),
    ]

    subpage_types = ["working_at_dit.Topic"]


class Topic(ContentPage):
    subpage_types = []  # Should not be able to create children

    content_panels = ContentPage.content_panels + [
        InlinePanel('topic_themes', label='Themes'),
    ]


class TopicTheme(models.Model):
    topic = ParentalKey(
        'working_at_dit.Topic',
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


class PageTopic(models.Model):
    page = ParentalKey(
        'content.ContentPage',
        on_delete=models.CASCADE,
        related_name='topics',
    )

    topic = models.ForeignKey(
        'working_at_dit.Topic',
        on_delete=models.CASCADE,
        related_name='topic_Pages',
    )

    panels = [
        PageChooserPanel('topic'),
    ]

    class Meta:
        unique_together = ('page', 'topic')


class PageWithTopics(ContentPage):
    content_panels = ContentPage.content_panels + [
        InlinePanel('topics', label="Topics"),
    ]
