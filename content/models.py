from typing import Optional

from bs4 import BeautifulSoup
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from simple_history.models import HistoricalRecords
from wagtail.admin.panels import FieldPanel
from wagtail.fields import StreamField
from wagtail.models import Page
from wagtail.search import index
from wagtail.snippets.models import register_snippet

from content import blocks
from content.utils import manage_excluded, manage_pinned
from core.utils import set_seen_cookie_banner
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


class ContentPage(BasePage):
    is_creatable = False
    show_in_menus = True

    # This field is used in search indexing as
    #  we can't change the search_analyzer property
    # of the default title field
    search_title = models.CharField(
        max_length=255,
    )

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

    body_no_html = models.TextField(
        blank=True,
        null=True,
    )

    @property
    def preview_text(self):
        if self.body_no_html:
            parts = self.body_no_html.split(" ")
            return " ".join(parts[0:40])

        return None

    subpage_types = []

    search_fields = Page.search_fields + [
        index.SearchField(
            "search_title",
            partial_match=True,
            boost=2,
            es_extra={
                "search_analyzer": "stop_and_synonyms",
            },
        ),
        index.SearchField(
            "body_no_html",
            partial_match=True,
            es_extra={
                "search_analyzer": "stop_and_synonyms",
            },
        ),
        index.AutocompleteField("body_no_html"),
        index.AutocompleteField("search_title"),
        index.FilterField("slug"),
    ]

    content_panels = Page.content_panels + [
        FieldPanel("body"),
    ]

    promote_panels = [
        FieldPanel("slug"),
        FieldPanel("show_in_menus"),
        FieldPanel("pinned_phrases"),
        FieldPanel("excluded_phrases"),
    ]

    def full_clean(self, *args, **kwargs):
        # Required so we can override
        # search analyzer (see above)
        self.search_title = self.title

        super().full_clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        body_string = str(self.body)

        self.body_no_html = BeautifulSoup(body_string, "html.parser").text

        # Required so we can override
        # search analyzer (see above)
        # self.search_title = self.title #

        if self.id:
            manage_excluded(self, self.excluded_phrases)
            manage_pinned(self, self.pinned_phrases)

        return super().save(*args, **kwargs)

    #
    # def get_children(self):
    #     children = super().get_children()
    #     return children.order_by('-last_published_at')


class SearchKeywordOrPhrase(models.Model):
    keyword_or_phrase = models.CharField(max_length=1000)
    history = HistoricalRecords()


class SearchExclusionPageLookUp(models.Model):
    search_keyword_or_phrase = models.ForeignKey(
        SearchKeywordOrPhrase,
        on_delete=models.CASCADE,
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    history = HistoricalRecords()


class SearchPinPageLookUp(models.Model):
    search_keyword_or_phrase = models.ForeignKey(
        SearchKeywordOrPhrase,
        on_delete=models.CASCADE,
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
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
