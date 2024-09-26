import logging

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from content.models.base_content import BasePage
from simple_history.models import HistoricalRecords
from wagtail.admin.panels import FieldPanel
from wagtail.fields import StreamField

import dw_design_system.dwds.components as dwds_blocks
from content.utils import get_search_content_for_block
from extended_search.index import DWIndexedField as IndexedField
from search.utils import split_query

logger = logging.getLogger(__name__)


class SearchFieldsMixin(models.Model):
    """
    Specific fields and settings to manage search. Extra fields are generally
    defined to make custom and specific indexing as defined in /docs/search.md

    Usage:
    - Add this mixin to a model
    - Define the fields that should be indexed in search_stream_fields.
      Example: ["body"]
    - Add SearchFieldsMixin.indexed_fields to the Model's indexed_fields list
    - Run self._generate_search_field_content() in full_clean() to generate
      search fields
    """

    class Meta:
        abstract = True

    search_stream_fields: list[str] = []

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

    def _generate_search_field_content(self):
        self.search_title = self.title
        search_headings = []
        search_content = []

        for stream_field_name in self.search_stream_fields:
            stream_field = getattr(self, stream_field_name)
            for stream_child in stream_field:
                block_search_headings, block_search_content = (
                    get_search_content_for_block(stream_child.block, stream_child.value)
                )
                search_headings += block_search_headings
                search_content += block_search_content

        self.search_headings = " ".join(search_headings)
        self.search_content = " ".join(search_content)

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
            "search_content",
            tokenized=True,
            explicit=True,
        ),
    ]


class SearchKeywordOrPhrase(models.Model):
    keyword_or_phrase = models.CharField(max_length=1000)
    # TODO: Remove historical records.
    history = HistoricalRecords()


class SearchKeywordOrPhraseQuerySet(models.QuerySet):
    def filter_by_query(self, query):
        query_parts = split_query(query)

        return self.filter(search_keyword_or_phrase__keyword_or_phrase__in=query_parts)


class NavigationPage(SearchFieldsMixin, BasePage):
    template = "content/navigation_page.html"

    search_stream_fields: list[str] = ["primary_elements", "secondary_elements"]

    primary_elements = StreamField(
        [
            ("dw_navigation_card", dwds_blocks.NavigationCardBlock()),
        ],
        blank=True,
    )

    secondary_elements = StreamField(
        [
            ("dw_curated_page_links", dwds_blocks.CustomPageLinkListBlock()),
            ("dw_tagged_page_list", dwds_blocks.TaggedPageListBlock()),
            ("dw_cta", dwds_blocks.CTACardBlock()),
            ("dw_engagement_card", dwds_blocks.EngagementCardBlock()),
            ("dw_navigation_card", dwds_blocks.NavigationCardBlock()),
        ],
        blank=True,
    )

    content_panels = BasePage.content_panels + [
        FieldPanel("primary_elements"),
        FieldPanel("secondary_elements"),
    ]

    indexed_fields = SearchFieldsMixin.indexed_fields + [
        IndexedField("primary_elements"),
        IndexedField("secondary_elements"),
    ]

    def get_template(self, request, *args, **kwargs):
        return self.template

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        return context

    def full_clean(self, *args, **kwargs):
        self._generate_search_field_content()
        super().full_clean(*args, **kwargs)


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