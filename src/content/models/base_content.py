import html
import logging
from typing import Optional

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q, Subquery
from django.forms import widgets
from django.utils import timezone
from django.utils.html import strip_tags
from simple_history.models import HistoricalRecords
from wagtail.admin.panels import (
    FieldPanel,
    InlinePanel,
    ObjectList,
    TabbedInterface,
    TitleFieldPanel,
)
from wagtail.admin.widgets.slug import SlugInput
from wagtail.fields import StreamField
from wagtail.models import Page, PageManager, PageQuerySet
from wagtail.snippets.models import register_snippet
from wagtail.utils.decorators import cached_classmethod

from content import blocks as content_blocks
from content.models.search import (
    SearchExclusionPageLookUp,
    SearchFieldsMixin,
    SearchPinPageLookUp,
)
from content.utils import (
    manage_excluded,
    manage_pinned,
    truncate_words_and_chars,
)
from content.validators import validate_description_word_count
from extended_search.index import DWIndexedField as IndexedField
from extended_search.index import Indexed, RelatedFields
from peoplefinder.widgets import PersonChooser
from user.models import User as UserModel

from .search import (
    SearchExclusionPageLookUp,
    SearchFieldsMixin,
    SearchPinPageLookUp,
)


logger = logging.getLogger(__name__)

User = get_user_model()

RICH_TEXT_FEATURES = [
    "ol",
    "ul",
    "link",
    "document-link",
    "anchor-identifier",
]


def strip_tags_with_spaces(string):
    spaced = string.replace("><", "> <")
    return strip_tags(spaced)


@register_snippet
class Theme(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    summary = models.CharField(max_length=255)
    history = HistoricalRecords()

    def __str__(self):
        return self.title

    panels = [
        FieldPanel("title"),
        FieldPanel("summary"),
    ]

    class Meta:
        ordering = ["-title"]


class BasePageQuerySet(PageQuerySet):
    def restricted_q(self, restriction_type):
        from wagtail.models import BaseViewRestriction, PageViewRestriction

        if isinstance(restriction_type, str):
            restriction_type = [
                restriction_type,
            ]

        RESTRICTION_CHOICES = BaseViewRestriction.RESTRICTION_CHOICES
        types = [t for t, _ in RESTRICTION_CHOICES if t in restriction_type]

        q = Q()
        for restriction in (
            PageViewRestriction.objects.filter(restriction_type__in=types)
            .select_related("page")
            .all()
        ):
            q |= self.descendant_of_q(restriction.page, inclusive=True)

        return q if q else Q(pk__in=[])

    def public_or_login(self):
        return self.exclude(self.restricted_q(["password", "groups"]))

    def pinned_q(self, query):
        pinned = SearchPinPageLookUp.objects.filter_by_query(query)

        return Q(pk__in=Subquery(pinned.values("object_id")))

    def pinned(self, query):
        return self.filter(self.pinned_q(query))

    def not_pinned(self, query):
        return self.exclude(self.pinned_q(query))

    def exclusions_q(self, query):
        exclusions = SearchExclusionPageLookUp.objects.filter_by_query(query)

        return Q(pk__in=Subquery(exclusions.values("object_id")))

    def exclusions(self, query):
        return self.filter(self.exclusions_q(query))

    def annotate_with_total_views(self):
        return self.annotate(
            total_views=models.Sum(
                "interactions_recentpageviews__count",
                distinct=True,
            )
        )

    def annotate_with_unique_views_all_time(self):
        return self.annotate(
            unique_views_all_time=models.Count(
                "interactions_recentpageviews",
                distinct=True,
            )
        )

    def annotate_with_unique_views_past_month(self):
        return self.annotate(
            unique_views_past_month=models.Count(
                "interactions_recentpageviews",
                filter=Q(
                    interactions_recentpageviews__updated_at__gte=timezone.now()
                    - timezone.timedelta(weeks=4)
                ),
                distinct=True,
            )
        )

    def order_by_most_recent_unique_views_past_month(self):
        return self.annotate_with_unique_views_past_month().order_by(
            "-unique_views_past_month"
        )


class BasePage(Page, Indexed):
    class Meta:
        permissions = [
            ("view_info_page", "Can view the info page in the Wagtail admin"),
        ]

    objects = PageManager.from_queryset(BasePageQuerySet)()

    legacy_path = models.CharField(
        max_length=500,
        blank=True,
        null=True,
    )

    promote_panels = []
    content_panels = [
        TitleFieldPanel("title"),
    ]

    @property
    def published_date(self):
        return self.last_published_at

    def get_first_publisher(self) -> Optional[UserModel]:
        """Return the first publisher of the page or None."""
        first_revision_with_user = (
            self.revisions.exclude(user=None).order_by("created_at", "id").first()
        )

        if first_revision_with_user:
            return first_revision_with_user.user
        else:
            return None

    @property
    def days_since_last_published(self):
        if self.last_published_at:
            result = timezone.now() - self.last_published_at
            return result.days
        return None


class ContentPageQuerySet(BasePageQuerySet):
    def annotate_with_comment_count(self):
        return self.annotate(comment_count=models.Count("comments"))


class ContentOwnerMixin(models.Model):
    content_owner = models.ForeignKey(
        "peoplefinder.Person",
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
    )
    content_contact_email = models.EmailField(
        help_text="Contact email shown on article, this could be the content owner or a team inbox",
        null=True,
        blank=False,
    )

    content_owner_panels = [
        FieldPanel("content_owner", widget=PersonChooser),
        FieldPanel("content_contact_email"),
    ]

    # This should be imported in the model that uses this mixin, e.g: Network.indexed_fields = [ ... ] + ContentOwnerMixin.indexed_fields
    indexed_fields = [
        RelatedFields(
            "content_owner",
            [
                IndexedField("first_name", explicit=True),
                IndexedField("preferred_first_name", explicit=True),
                IndexedField("last_name", explicit=True),
            ],
        ),
        IndexedField("content_contact_email", explicit=True),
    ]

    @cached_classmethod
    def get_edit_handler(cls):
        return TabbedInterface(
            [
                ObjectList(cls.content_panels, heading="Content"),
                ObjectList(cls.promote_panels, heading="Promote"),
                ObjectList(cls.content_owner_panels, heading="Content owner"),
            ]
        ).bind_to_model(cls)

    class Meta:
        abstract = True

    @classmethod
    def get_all_subclasses(cls):
        subclasses = []
        direct_subclasses = cls.__subclasses__()

        for direct_subclass in direct_subclasses:
            subclasses.append(direct_subclass)
            subclasses.extend(direct_subclass.get_all_subclasses())

        return subclasses


class ContentPage(SearchFieldsMixin, BasePage):
    objects = PageManager.from_queryset(ContentPageQuerySet)()

    is_creatable = False
    show_in_menus = True
    search_stream_fields = ["body"]

    legacy_guid = models.CharField(
        blank=True, null=True, max_length=255, help_text="""Wordpress GUID"""
    )

    legacy_content = models.TextField(
        blank=True, null=True, help_text="""Legacy content, pre-conversion"""
    )

    description = models.TextField(
        blank=True,
        null=True,
        help_text="Please use this field only to add a description for an event.",
        validators=[validate_description_word_count],
    )

    preview_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    body = StreamField(
        [
            ("heading2", content_blocks.Heading2Block()),
            ("heading3", content_blocks.Heading3Block()),
            ("heading4", content_blocks.Heading4Block()),
            ("heading5", content_blocks.Heading5Block()),
            (
                "text_section",
                content_blocks.TextBlock(
                    blank=True,
                    features=RICH_TEXT_FEATURES,
                    help_text="""Some text to describe what this section is about (will be
            displayed above the list of child pages)""",
                ),
            ),
            ("image", content_blocks.ImageBlock()),
            (
                "embed_video",
                content_blocks.EmbedVideoBlock(help_text="""Embed a video"""),
            ),
            (
                "media",
                content_blocks.InternalMediaBlock(
                    help_text="""Link to a media block"""
                ),
            ),
            (
                "data_table",
                content_blocks.DataTableBlock(
                    help_text="""ONLY USE THIS FOR TABLULAR DATA, NOT FOR FORMATTING"""
                ),
            ),
        ],
        use_json_field=True,
    )

    excerpt = models.CharField(
        max_length=700,
        blank=True,
        null=True,
        help_text=(
            "A summary of the page to be shown in search results. (making this"
            " field empty will result in an autogenerated excerpt)"
        ),
    )

    pinned_phrases = models.CharField(
        blank=True,
        null=True,
        max_length=1000,
        help_text="A comma separated list of pinned keywords and phrases. "
        "Do not use quotes for phrases. The page will be pinned "
        "to the first page of search results for these terms.",
    )

    excluded_phrases = models.CharField(
        blank=True,
        null=True,
        max_length=1000,
        help_text="A comma separated list of excluded keywords and phrases. "
        "Do not use quotes for phrases. The page will be removed "
        "from search results for these terms",
    )

    #
    # Topics
    # This would ideally belong on PageWithTopics, but the Network model uses it
    # and it's not worth the effort to refactor it.
    #

    @property
    def topics(self):
        from working_at_dit.models import Topic

        # This needs to be a list comprehension to work nicely with modelcluster.
        topic_ids = [page_topic.topic.pk for page_topic in self.page_topics.all()]
        return Topic.objects.filter(pk__in=topic_ids)

    @property
    def topic_titles(self):
        return [topic.title for topic in self.topics]

    #
    # Search
    # Specific fields and settings to manage search. Extra fields are generally
    # defined to make custom and specific indexing as defined in /docs/search.md
    #

    indexed_fields = SearchFieldsMixin.indexed_fields + [
        IndexedField(
            "excerpt",
            tokenized=True,
            explicit=True,
            boost=2.0,
        ),
        IndexedField("is_creatable", filter=True),
        IndexedField(
            "description",
            tokenized=True,
            explicit=True,
        ),
    ]

    #
    # Wagtail admin configuration
    #

    subpage_types = []

    content_panels = BasePage.content_panels + [
        FieldPanel("description"),
        FieldPanel("body"),
        FieldPanel("excerpt", widget=widgets.Textarea),
        FieldPanel("preview_image"),
        InlinePanel("tagged_items", label="Tags"),
    ]

    promote_panels = [
        FieldPanel("slug", widget=SlugInput),
        FieldPanel("show_in_menus"),
        FieldPanel("pinned_phrases"),
        FieldPanel("excluded_phrases"),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        tag_set = []
        # TODO: Enable when we want to show tags to users.
        # for tagged_item in self.tagged_items.select_related("tag").all():
        #     tag_set.append(tagged_item.tag)
        context["tag_set"] = tag_set

        return context

    def full_clean(self, *args, **kwargs):
        self._generate_search_field_content()
        if self.excerpt is None:
            self._generate_excerpt()

        super().full_clean(*args, **kwargs)

    def _generate_excerpt(self):
        content = "".join(
            [str(b.value) for b in self.body if b.block_type == "text_section"]
        )
        self.excerpt = truncate_words_and_chars(
            html.unescape(strip_tags_with_spaces(content)), 40, 700
        )

    def save(self, *args, **kwargs):
        if self.excerpt is None:
            self._generate_excerpt()

        if self.id:
            manage_excluded(self, self.excluded_phrases)
            manage_pinned(self, self.pinned_phrases)

        return super().save(*args, **kwargs)
