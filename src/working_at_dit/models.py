from itertools import groupby

from django.db import models
from django.db.models import Q
from modelcluster.fields import ParentalKey

from content.imports.mappers import ContentPageMapper
from content.models import BasePage, ContentOwnerMixin, ContentPage, Theme
from core.panels import FieldPanel, InlinePanel
from extended_search.index import DWIndexedField as IndexedField


class WorkingAtDITHome(ContentPage):
    panels = [
        FieldPanel("name"),
        FieldPanel("body"),
    ]

    subpage_types = [
        "working_at_dit.Topic",
        "working_at_dit.HowDoI",
        "content.NavigationPage",
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        context["themes"] = Theme.objects.all().order_by("title")

        return context


class Topic(ContentOwnerMixin, ContentPage):
    subpage_types = []  # Should not be able to create children

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        context["attribution"] = True

        context["related_news"] = PageTopic.objects.filter(
            topic=self, page__content_type__app_label="news"
        ).order_by("-page__last_published_at")[:5]

        context["policies_and_guidance"] = (
            ContentPage.objects.public()
            .live()
            .filter(
                page_topics__topic=self,
                content_type__app_label="working_at_dit",
            )
            .filter(Q(content_type__model="policy") | Q(content_type__model="guidance"))
            .order_by("-last_published_at")
        )

        tools = PageTopic.objects.filter(
            topic=self, page__content_type__app_label="tools"
        ).order_by("page__last_published_at")

        context["tools"] = tools

        how_do_is = PageTopic.objects.filter(
            topic=self,
            page__content_type__app_label="working_at_dit",
            page__content_type__model="howdoi",
            page__live=True,
        ).order_by("page__last_published_at")

        context["how_do_is"] = how_do_is

        return context

    content_panels = ContentPage.content_panels + [
        InlinePanel("topic_themes", label="Themes"),
    ]

    indexed_fields = ContentOwnerMixin.indexed_fields


class TopicHome(BasePage):
    template = "content/content_page.html"
    subpage_types = ["working_at_dit.Topic"]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["children"] = Topic.objects.live().public().order_by("title")
        context["display"] = "basic"
        context["bookmark"] = True

        return context


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
        FieldPanel("theme"),
    ]

    class Meta:
        unique_together = ("topic", "theme")
        ordering = ["topic__title"]


class PageTopic(models.Model):
    page = ParentalKey(
        "content.ContentPage",
        on_delete=models.CASCADE,
        related_name="page_topics",
    )

    topic = models.ForeignKey(
        "working_at_dit.Topic",
        on_delete=models.CASCADE,
        related_name="topic_pages",
    )

    panels = [
        FieldPanel("topic"),
    ]

    class Meta:
        unique_together = ("page", "topic")


# TODO: Possibly remove this page type in the hierarchy? (lots of work!)
class PageWithTopics(ContentPage):
    indexed_fields = [
        IndexedField(
            "topic_titles",
            tokenized=True,
            explicit=True,
        ),
    ]

    content_panels = ContentPage.content_panels + [
        InlinePanel("page_topics", label="Topics"),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["page_topics"] = self.page_topics.order_by("topic__title")
        return context


class HowDoI(ContentOwnerMixin, PageWithTopics):
    template = "working_at_dit/content_with_related_topics.html"
    subpage_types = []  # Should not be able to create children

    include_link_on_homepage = models.BooleanField(
        default=False,
    )

    content_panels = PageWithTopics.content_panels + [
        FieldPanel("include_link_on_homepage"),
    ]

    indexed_fields = ContentOwnerMixin.indexed_fields

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["attribution"] = True
        return context


class HowDoIHome(ContentPage):
    template = "content/content_page.html"
    subpage_types = ["working_at_dit.HowDoI"]  # Should not be able to create children

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        context["children"] = HowDoI.objects.live().public().order_by("title")
        context["display"] = "basic"
        context["bookmark"] = True

        return context


class Guidance(ContentOwnerMixin, PageWithTopics):
    template = "working_at_dit/content_with_related_topics.html"
    is_creatable = True

    subpage_types = ["working_at_dit.Guidance"]

    indexed_fields = ContentOwnerMixin.indexed_fields

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["attribution"] = True
        return context


class Policy(ContentOwnerMixin, PageWithTopics):
    mapper_class = ContentPageMapper

    template = "working_at_dit/content_with_related_topics.html"
    is_creatable = True

    subpage_types = ["working_at_dit.Policy"]

    indexed_fields = ContentOwnerMixin.indexed_fields

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["attribution"] = True
        return context


class PoliciesHome(BasePage):
    template = "working_at_dit/section_home_alpha_order.html"
    subpage_types = [
        "working_at_dit.Policy",
    ]
    is_creatable = False

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        policies = list(Policy.objects.live().public().order_by("title"))
        context["subpage_groups"] = [
            list(g) for k, g in groupby(policies, key=lambda x: x.title.lower()[0])
        ]

        return context


class GuidanceHome(BasePage):
    template = "working_at_dit/section_home_alpha_order.html"
    subpage_types = [
        "working_at_dit.Guidance",
    ]
    is_creatable = False

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        guidance = list(Guidance.objects.live().public().order_by("title"))
        context["subpage_groups"] = [
            list(g) for k, g in groupby(guidance, key=lambda x: x.title.lower()[0])
        ]

        return context


class PoliciesAndGuidanceHome(BasePage):
    template = "content/content_page.html"
    subpage_types = [
        "working_at_dit.PoliciesHome",
        "working_at_dit.GuidanceHome",
    ]
    is_creatable = False

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["children"] = [
            PoliciesHome.objects.live().public().first(),
            GuidanceHome.objects.live().public().first(),
        ]
        context["display"] = "basic"
        context["bookmark"] = True

        return context
