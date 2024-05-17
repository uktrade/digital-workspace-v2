from wagtail import blocks


class CustomPageLinkListBlock(blocks.StructBlock):
    class Meta:
        template = "dwds/components/link_list.html"
        label = "Link list"
        help_text = "List of links to specific pages"

    title = blocks.CharBlock(
        label="Title",
        icon="title",
        classname="full title",
        max_length=40,
        search_index=False,
    )
    description = blocks.CharBlock(required=False, max_length=40)
    pages = blocks.ListBlock(blocks.PageChooserBlock(label="Page"), search_index=False)

    def get_context(self, value, parent_context=None):
        context = parent_context or {}
        context.update(
            title=value["title"],
            description=value["description"],
            list=[
                {"url": page.get_url(), "text": page.title} for page in value["pages"]
            ],
        )
        return context


# Old blocks not to be used for dwds link list component.
class TitleBlock(blocks.CharBlock):
    """A (section) heading"""

    class Meta:
        label = "Title"
        icon = "title"
        classname = "full title"
        template = "blocks/title.html"


class PagePickerBlock(blocks.PageChooserBlock):

    class Meta:
        label = "Link"
