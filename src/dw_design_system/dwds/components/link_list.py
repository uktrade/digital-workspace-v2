from wagtail import blocks


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


class CustomPageLinkListBlock(blocks.StructBlock):
    class Meta:
        template = "dwds/components/link_list.html"
        label = "Link list"
        help_text = "List of links to specific pages"

    title = TitleBlock(search_index=False)
    pages = blocks.ListBlock(PagePickerBlock(), search_index=False)

    def get_context(self, value, parent_context=None):
        context = parent_context or {}
        context.update(
            {
                "title": value["title"],
                "list": [
                    {"url": page.get_url(), "text": page.title}
                    for page in value["pages"]
                ],
            }
        )
        return context
