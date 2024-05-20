# Don't use these blocks! They can be deleted after we squash the migrations.

from wagtail import blocks


class TitleBlock(blocks.CharBlock):
    """A (section) heading"""

    class Meta:
        label = "Title"
        icon = "title"
        classname = "full title"
        template = "archived_blocks/title.html"


class PagePickerBlock(blocks.PageChooserBlock):
    class Meta:
        label = "Link"


class CustomPageLinkListBlock(blocks.StructBlock):
    title = TitleBlock(search_index=False)
    pages = blocks.ListBlock(PagePickerBlock(), search_index=False)

    class Meta:
        template = "archived_blocks/custom_page_link_list.html"
        label = "Link box"
        help_text = "Test"
