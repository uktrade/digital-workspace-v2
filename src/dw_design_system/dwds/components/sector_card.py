from wagtail import blocks

import dw_design_system.dwds.components as dwds_blocks
from content import blocks as content_blocks


class SectorCardBlock(blocks.StructBlock):
    """Sector section"""

    sector_title = content_blocks.HeadingBlock(required=True, max_length=30)
    sector_elements = blocks.StreamBlock(
        [
            ("dw_navigation_card", dwds_blocks.NavigationCardBlock()),
        ],
        required=True,
        label="Sector Elements",
    )

    class Meta:
        template = "dwds/components/sector_card.html"
        icon = "form"
        label = "Sector with elements"

    def get_context(self, value, parent_context=None):
        context = parent_context or {}

        context.update(
            sector_title=value["sector_title"],
            sector_elements=value["sector_elements"],
        )
        return context

    def get_searchable_heading(self, value):
        title = value["sector_title"]
        return title
