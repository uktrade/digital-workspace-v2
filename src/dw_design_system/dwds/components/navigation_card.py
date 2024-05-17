from wagtail import blocks


class NavigationCardBlock(blocks.StructBlock):
    """A nav card to direct users"""

    title = blocks.CharBlock(required=True)
    url = blocks.URLBlock(required=True)
    summary = blocks.CharBlock(required=False, max_length=50)

    class Meta:
        label = "Navigation Card"
        icon = "link"
        template = "dwds/components/navigation_card.html"
