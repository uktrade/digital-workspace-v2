from wagtail import blocks


class NavigationCardBlock(blocks.StructBlock):
    """A nav card to direct users"""

    title = blocks.CharBlock(required=True)
    page = blocks.PageChooserBlock(required=True)
    summary = blocks.CharBlock(required=False, max_length=50)

    class Meta:
        label = "Navigation Card"
        icon = "link"
        template = "dwds/components/navigation_card.html"

    def get_context(self, value, parent_context=None):
        context = parent_context or {}
        context.update(
            title=value["title"],
            url=value["page"].get_url(),
            summary=value["summary"],
        )
        return context
