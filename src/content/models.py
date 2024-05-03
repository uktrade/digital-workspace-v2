import html
from typing import Optional

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q, Subquery
from django.forms import widgets
from django.utils import timezone
from django.utils.html import strip_tags
from simple_history.models import HistoricalRecords
from wagtail.admin.panels import (
    FieldPanel,
    ObjectList,
    TabbedInterface,
    TitleFieldPanel,
)
from wagtail.admin.widgets.slug import SlugInput
from wagtail.fields import StreamField
from wagtail.models import Page, PageManager, PageQuerySet
from wagtail.snippets.models import register_snippet
from wagtail.utils.decorators import cached_classmethod

from content import blocks
from content.utils import manage_excluded, manage_pinned, truncate_words_and_chars
from core.utils import set_seen_cookie_banner
from extended_search.index import DWIndexedField as IndexedField
from extended_search.index import Indexed
from peoplefinder.widgets import PersonChooser
from search.utils import split_query
from user.models import User as UserModel


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


class BasePage(Page, Indexed):
    legacy_path = models.CharField(
        max_length=500,
        blank=True,
        null=True,
    )

    promote_panels = []
    content_panels = [
        TitleFieldPanel("title"),
    ]

    def serve(self, request):
        response = super().serve(request)
        set_seen_cookie_banner(request, response)

        return response

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


class ContentPageQuerySet(PageQuerySet):
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

    def pinned_q(self, query):
        pinned = SearchPinPageLookUp.objects.filter_by_query(query)

        return Q(pk__in=Subquery(pinned.values("object_id")))

    def public_or_login(self):
        return self.exclude(self.restricted_q(["password", "groups"]))

    def pinned(self, query):
        return self.filter(self.pinned_q(query))

    def not_pinned(self, query):
        return self.exclude(self.pinned_q(query))

    def exclusions_q(self, query):
        exclusions = SearchExclusionPageLookUp.objects.filter_by_query(query)

        return Q(pk__in=Subquery(exclusions.values("object_id")))

    def exclusions(self, query):
        return self.filter(self.exclusions_q(query))


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


class ContentPage(BasePage):
    objects = PageManager.from_queryset(ContentPageQuerySet)()

    is_creatable = False
    show_in_menus = True

    legacy_guid = models.CharField(
        blank=True, null=True, max_length=255, help_text="""Wordpress GUID"""
    )

    legacy_content = models.TextField(
        blank=True, null=True, help_text="""Legacy content, pre-conversion"""
    )

    body = StreamField(
        [
            ("heading2", blocks.Heading2Block()),
            ("heading3", blocks.Heading3Block()),
            ("heading4", blocks.Heading4Block()),
            ("heading5", blocks.Heading5Block()),
            (
                "text_section",
                blocks.TextBlock(
                    blank=True,
                    features=RICH_TEXT_FEATURES,
                    help_text="""Some text to describe what this section is about (will be
            displayed above the list of child pages)""",
                ),
            ),
            ("image", blocks.ImageBlock()),
            ("embed_video", blocks.EmbedVideoBlock(help_text="""Embed a video""")),
            ("media", blocks.InternalMediaBlock(help_text="""Link to a media block""")),
            (
                "data_table",
                blocks.DataTableBlock(
                    help_text="""ONLY USE THIS FOR TABLULAR DATA, NOT FOR FORMATTING"""
                ),
            ),
            (
                "cta",
                blocks.CTABlock(
                    help_text="""The CTA button is an eye-catching link designed to direct users to a specific page or URL. You can define the label for the button below, as well as the page or URL to which you want the button to point. Please use this component sparingly."""
                ),
            ),
        ],
        use_json_field=True,
    )

    custom_page_links = StreamField(
        [
            ("page_links", blocks.CustomPageLinkListBlock()),
        ],
        blank=True,
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
    # Search
    # Specific fields and settings to manage search. Extra fields are generally
    # defined to make custom and specific indexing as defined in /docs/search.md
    #

    search_title = models.CharField(
        max_length=255,
    )

    search_headings = models.TextField(
        blank=True,
        null=True,
    )

    search_content = models.TextField(
        blank=True,
        null=True,
    )

    indexed_fields = [
        IndexedField(
            "search_title",
            tokenized=True,
            explicit=True,
            fuzzy=True,
            boost=5.0,
        ),
        IndexedField(
            "search_headings",
            tokenized=True,
            explicit=True,
            fuzzy=True,
            boost=3.0,
        ),
        IndexedField(
            "excerpt",
            tokenized=True,
            explicit=True,
            boost=2.0,
        ),
        IndexedField(
            "search_content",
            tokenized=True,
            explicit=True,
        ),
        IndexedField("is_creatable", filter=True),
        IndexedField("published_date", proximity=True),
    ]

    @property
    def published_date(self):
        return self.last_published_at

    def _generate_search_field_content(self):
        self.search_title = self.title
        self.search_headings = ""
        self.search_content = ""
        for block in self.body:
            if block.block_type in ["heading2", "heading3", "heading4", "heading5"]:
                self.search_headings += f" {strip_tags(block.value)}"
            elif block.block_type == "text_section":
                self.search_content += f" {strip_tags_with_spaces(str(block.value))}"
            elif block.block_type == "image":
                self.search_content += f" {block.value['caption']}"

    #
    # Wagtail admin configuration
    #

    subpage_types = []

    content_panels = BasePage.content_panels + [
        FieldPanel("excerpt", widget=widgets.Textarea),
        FieldPanel("custom_page_links"),
        FieldPanel("body"),
    ]

    promote_panels = [
        FieldPanel("slug", widget=SlugInput),
        FieldPanel("show_in_menus"),
        FieldPanel("pinned_phrases"),
        FieldPanel("excluded_phrases"),
    ]

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


class SearchKeywordOrPhrase(models.Model):
    keyword_or_phrase = models.CharField(max_length=1000)
    # TODO: Remove historical records.
    history = HistoricalRecords()


class SearchKeywordOrPhraseQuerySet(models.QuerySet):
    def filter_by_query(self, query):
        query_parts = split_query(query)

        return self.filter(search_keyword_or_phrase__keyword_or_phrase__in=query_parts)


class CustomServicePage(ContentPage):
    template = "content/content_page.html"
    subpage_types = []
    
    primary = StreamField(
        [
            ("page_links", blocks.CustomPageLinkListBlock()),
        ],
        blank=True,
    )

    secondary = StreamField(
        [
            ("page_links", blocks.CustomPageLinkListBlock()),
        ],
        blank=True,
    )

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        return context


class SearchExclusionPageLookUp(models.Model):
    objects = SearchKeywordOrPhraseQuerySet.as_manager()

    search_keyword_or_phrase = models.ForeignKey(
        SearchKeywordOrPhrase,
        on_delete=models.CASCADE,
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    # TODO: Remove historical records.
    history = HistoricalRecords()


class SearchPinPageLookUp(models.Model):
    objects = SearchKeywordOrPhraseQuerySet.as_manager()

    search_keyword_or_phrase = models.ForeignKey(
        SearchKeywordOrPhrase,
        on_delete=models.CASCADE,
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    # TODO: Remove historical records.
    history = HistoricalRecords()
