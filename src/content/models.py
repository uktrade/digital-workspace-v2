from typing import Optional

from bs4 import BeautifulSoup
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q, Subquery
from django.forms import widgets
from simple_history.models import HistoricalRecords
from wagtail.admin.panels import FieldPanel
from wagtail.fields import StreamField
from wagtail.models import Page, PageManager, PageQuerySet
from wagtail.search import index
from wagtail.snippets.models import register_snippet

from content import blocks
from content.utils import manage_excluded, manage_pinned, truncate_words_and_chars
from core.utils import set_seen_cookie_banner
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


class BasePage(Page):
    legacy_path = models.CharField(
        max_length=500,
        blank=True,
        null=True,
    )

    promote_panels = []

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


class ContentPageQuerySet(PageQuerySet):
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
        ],
        use_json_field=True,
    )

    excerpt = models.CharField(
        max_length=700,
        blank=True,
        null=True,
        help_text="A summary of the page to be shown in search results."
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

    search_fields = Page.search_fields + [
        index.SearchField(
            "search_title",
            es_extra={
                "search_analyzer": "simple",
            },
        ),
        index.SearchField(
            "search_headings",
            es_extra={
                "search_analyzer": "simple",
            },
        ),
        index.SearchField(
            "search_content",
            es_extra={
                "search_analyzer": "simple",
            },
        ),
        index.SearchField(
            "excerpt",
            es_extra={
                "search_analyzer": "simple",
            },
        ),
        index.AutocompleteField(
            "search_title",
            es_extra={
                "search_analyzer": "snowball",
            },
        ),
        index.AutocompleteField(
            "search_headings",
            es_extra={
                "search_analyzer": "snowball",
            },
        ),
        index.AutocompleteField(
            "search_content",
            es_extra={
                "search_analyzer": "snowball",
            },
        ),
        index.AutocompleteField(
            "excerpt",
            es_extra={
                "search_analyzer": "snowball",
            },
        ),
        index.FilterField("slug"),
        index.FilterField("is_creatable"),
    ]

    def _generate_search_field_content(self):
        body_string = str(self.body)
        soup = BeautifulSoup(body_string, "html.parser")
        self.search_title = self.title
        self.search_headings = " ".join(
            [tag.string or '' for tag in soup.find_all(
                ['h2', 'h3', 'h4', 'h5']
            )]
        )
        self.search_content = " ".join(
            [tag.string or '' for tag in soup.find_all(
                ['p', 'a', 'li', 'figcaption', 'blockquote', 'dd', 'dt']
            )]
        )

    #
    # Wagtail admin configuration
    #

    subpage_types = []

    content_panels = Page.content_panels + [
        FieldPanel("excerpt", widget=widgets.Textarea),
        FieldPanel("body"),
    ]

    promote_panels = [
        FieldPanel("slug"),
        FieldPanel("show_in_menus"),
        FieldPanel("pinned_phrases"),
        FieldPanel("excluded_phrases"),
    ]

    def full_clean(self, *args, **kwargs):
        self._generate_search_field_content()

        if self.excerpt is None:
            self.excerpt = truncate_words_and_chars(self.search_content, 40, 700)

        super().full_clean(*args, **kwargs)

    def save(self, *args, **kwargs):
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


class PrivacyPolicyHome(ContentPage):
    is_creatable = False

    subpage_types = [
        "content.PrivacyPolicy",
    ]

    template = "content/content_page.html"


class PrivacyPolicy(ContentPage):
    is_creatable = True

    subpage_types = []

    template = "content/content_page.html"
