from django.db import models

from wagtail.admin.edit_handlers import (
    FieldPanel,
    StreamFieldPanel,
    InlinePanel,
    PageChooserPanel,
)
from wagtail.core.models import Page
from wagtail.snippets.edit_handlers import SnippetChooserPanel

from modelcluster.fields import ParentalKey

from content.models import ContentPage


class WorkingAtDITHome(ContentPage):
    panels = [
        FieldPanel('name'),
        StreamFieldPanel('body'),
    ]

    subpage_types = ["working_at_dit.Topic", "working_at_dit.HowDoI", ]


class TopicHome(Page):
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


class HowDoIHome(ContentPage):
    subpage_types = ["working_at_dit.HowDoI"]  # Should not be able to create children


class HowDoI(PageWithTopics):
    subpage_types = []  # Should not be able to create children


class PoliciesAndGuidanceHome(Page):
    subpage_types = ["working_at_dit.PoliciesHome", "working_at_dit.GuidanceHome", ]
    # model just for use in editor hierarchy


class PoliciesHome(Page):
    subpage_types = ["working_at_dit.Policy", ]
    # model just for use in editor hierarchy


class GuidanceHome(Page):
    subpage_types = ["working_at_dit.Guidance", ]
    # model just for use in editor hierarchy


class Guidance(PageWithTopics):
    is_creatable = True

    subpage_types = ["working_at_dit.Guidance"]


class Policy(PageWithTopics):
    is_creatable = True

    subpage_types = ["working_at_dit.Policy"]
