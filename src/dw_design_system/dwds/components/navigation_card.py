from wagtail import blocks


class NavigationCardBlock(blocks.StructBlock):
    """A nav card to direct users"""

    page = blocks.PageChooserBlock()
    title = blocks.CharBlock(
        required=False,
        max_length=30,
        help_text="By default, the navigation card component will render the name of the page you linked above. If you have to change this behavior, add an ad hoc title in the box below. Please use sparingly.",
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
