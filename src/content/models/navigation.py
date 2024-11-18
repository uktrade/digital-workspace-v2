from wagtail.admin.panels import FieldPanel
from wagtail.fields import StreamField

import dw_design_system.dwds.components as dwds_blocks
from content.models import BasePage
from .search import SearchFieldsMixin
from extended_search.index import DWIndexedField as IndexedField


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
