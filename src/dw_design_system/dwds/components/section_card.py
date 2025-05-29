from wagtail import blocks

import dw_design_system.dwds.components as dwds_blocks
from content import blocks as content_blocks


class SectionCardBlock(blocks.StructBlock):
    """Section section"""

    section_title = content_blocks.HeadingBlock(required=False, max_length=30)
    section_elements = blocks.StreamBlock(
        [
            ("dw_navigation_card", dwds_blocks.NavigationCardBlock()),
        ],
        required=True,
        label="Section Elements",
    )

    class Meta:
        template = "dwds/components/section_card.html"
        icon = "form"
        label = "Section with elements"

    def get_context(self, value, parent_context=None):
        context = parent_context or {}

        context.update(
            section_title=value["section_title"],
            section_elements=value["section_elements"],
        )
        return context

    def get_searchable_heading(self, value):
        title = value["section_title"]
        return title
