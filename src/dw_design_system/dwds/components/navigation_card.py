from wagtail import blocks

from content import blocks as content_blocks


class NavigationCardBlock(blocks.StructBlock):
    """A nav card to direct users"""

    page = blocks.PageChooserBlock()
    title = content_blocks.HeadingBlock(
        required=False,
        max_length=30,
        help_text="By default, the name of the page will be the title. Override it using the below field.",
    )
    summary = blocks.CharBlock(required=False, max_length=70)

    class Meta:
        label = "Navigation Card"
        icon = "link"
        template = "dwds/components/navigation_card.html"

    def get_context(self, value, parent_context=None):
        context = parent_context or {}
        page = value["page"]
        context.update(
            title=value.get("title") or page.title,
            url=page.get_url(),
            summary=value["summary"],
        )
        return context

    def get_searchable_heading(self, value):
        title = value["title"]
        page = value["page"]
        return title or page.title
