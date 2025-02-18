from wagtail_content_import.mappers.converters import (
    ImageConverter,
    RichTextConverter,
    TableConverter,
    TextConverter,
)
from wagtail_content_import.mappers.streamfield import StreamFieldMapper


class ContentPageMapper(StreamFieldMapper):
    heading1 = TextConverter("heading1")
    heading2 = TextConverter("heading2")
    heading3 = TextConverter("heading3")
    heading4 = TextConverter("heading4")
    heading5 = TextConverter("heading5")
    html = RichTextConverter("text_section")
    image = ImageConverter("image")
    table = TableConverter("data_table")
