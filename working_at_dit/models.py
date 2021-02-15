from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.admin.edit_handlers import (
    FieldPanel,
    InlinePanel,
    PageChooserPanel,
    StreamFieldPanel,
)
from wagtail.snippets.edit_handlers import SnippetChooserPanel

from content.models import BasePage, ContentPage, Theme


class WorkingAtDITHome(ContentPage):
    panels = [
        FieldPanel("name"),
        StreamFieldPanel("body"),
    ]

    subpage_types = [
        "working_at_dit.Topic",
        "working_at_dit.HowDoI",
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        context["themes"] = Theme.objects.all().order_by("title")

        return context


class TopicHome(BasePage):
    subpage_types = ["working_at_dit.Topic"]


class Topic(ContentPage):
    subpage_types = []  # Should not be able to create children

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        context["related_news"] = PageTopic.objects.filter(
            topic=self.contentpage, page__content_type__app_label="news"
        ).order_by("-page__last_published_at")[:5]

        policies_and_guidance = PageTopic.objects.filter(
            topic=self.contentpage,
            page__content_type__app_label="working_at_dit",
        ).order_by("-page__last_published_at")

        policies_and_guidance = policies_and_guidance.filter(
            page__content_type__model="policy",
        ) | policies_and_guidance.filter(
            page__content_type__model="guidance",
        )

        context["policies_and_guidance"] = policies_and_guidance

        tools = PageTopic.objects.filter(
            topic=self.contentpage, page__content_type__app_label="tools"
        ).order_by("page__last_published_at")

        context["tools"] = tools

        how_do_is = PageTopic.objects.filter(
            topic=self.contentpage,
            page__content_type__app_label="working_at_dit",
            page__content_type__model="howdoi",
        ).order_by("page__last_published_at")

        context["how_do_is"] = how_do_is

        return context

    content_panels = ContentPage.content_panels + [
        InlinePanel("topic_themes", label="Themes"),
    ]


class TopicTheme(models.Model):
    topic = ParentalKey(
        "working_at_dit.Topic",
        on_delete=models.CASCADE,
        related_name="topic_themes",
    )

    theme = models.ForeignKey(
        "content.Theme",
        on_delete=models.CASCADE,
        related_name="theme_topics",
    )

    panels = [
        SnippetChooserPanel("theme"),
    ]

    class Meta:
        unique_together = ("topic", "theme")
        ordering = ["topic__title"]


class PageTopic(models.Model):
    page = ParentalKey(
        "content.ContentPage",
        on_delete=models.CASCADE,
        related_name="topics",
    )

    topic = models.ForeignKey(
        "working_at_dit.Topic",
        on_delete=models.CASCADE,
        related_name="topic_Pages",
    )

    panels = [
        PageChooserPanel("topic"),
    ]

    class Meta:
        unique_together = ("page", "topic")


class PageWithTopics(ContentPage):
    excerpt = models.CharField(max_length=600, blank=True, null=True)

    content_panels = ContentPage.content_panels + [
        FieldPanel("excerpt"),
        InlinePanel("topics", label="Topics"),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        context["page_topics"] = PageTopic.objects.filter(
            page=self,
        ).order_by("topic__title")

        return context


class HowDoI(PageWithTopics):
    subpage_types = []  # Should not be able to create children

    include_link_on_homepage = models.BooleanField(
        default=False,
    )

    content_panels = PageWithTopics.content_panels + [
        FieldPanel("include_link_on_homepage"),
    ]


class HowDoIHome(ContentPage):
    subpage_types = ["working_at_dit.HowDoI"]  # Should not be able to create children

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        context["how_do_i_pages"] = HowDoI.objects.live().public().order_by("title")

        return context


class Guidance(PageWithTopics):
    template = "working_at_dit/policy_guidance.html"
    is_creatable = True

    subpage_types = ["working_at_dit.Guidance"]


class Policy(PageWithTopics):
    template = "working_at_dit/policy_guidance.html"
    is_creatable = True

    subpage_types = ["working_at_dit.Policy"]


class PoliciesAndGuidanceHome(BasePage):
    subpage_types = [
        "working_at_dit.PoliciesHome",
        "working_at_dit.GuidanceHome",
    ]
    # model just for use in editor hierarchy


class PoliciesHome(BasePage):
    subpage_types = [
        "working_at_dit.Policy",
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["policies"] = Policy.objects.live().public().order_by("title")

        return context


class GuidanceHome(BasePage):
    subpage_types = [
        "working_at_dit.Guidance",
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["guidances"] = Guidance.objects.live().public().order_by("title")

        return context
