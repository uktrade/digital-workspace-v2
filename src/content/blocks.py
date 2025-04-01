from django.core.exceptions import ValidationError
from wagtail import blocks
from wagtail.contrib.table_block.blocks import TableBlock
from wagtail.embeds.blocks import EmbedBlock
from wagtail.images.blocks import ImageChooserBlock
from wagtailmedia.blocks import AbstractMediaChooserBlock

from peoplefinder.blocks import PersonChooserBlock


RICH_TEXT_FEATURES = [
    "ol",
    "ul",
    "link",
    "document-link",
    "anchor-identifier",
]


class HeadingBlock(blocks.CharBlock):
    """A (section) heading
    Base block used to provide functionality for all heading blocks

    Usage:
    - If you know the heading level you want, use the appropriate block,
      otherwise use this block
    """

    ...


class Heading2Block(HeadingBlock):
    """A (section) heading"""

    class Meta:
        label = "Heading 2"
        icon = "title"
        classname = "full title"
        template = "blocks/heading_2.html"


class Heading3Block(HeadingBlock):
    """A (section) heading"""

    class Meta:
        label = "Heading 3"
        icon = "title"
        classname = "full title"
        template = "blocks/heading_3.html"


class Heading4Block(HeadingBlock):
    """A (section) heading"""

    class Meta:
        label = "Heading 4"
        icon = "title"
        classname = "full title"
        template = "blocks/heading_4.html"


class Heading5Block(HeadingBlock):
    """A (section) heading"""

    class Meta:
        label = "Heading 5"
        icon = "title"
        classname = "full title"
        template = "blocks/heading_5.html"


class TextBlock(blocks.RichTextBlock):
    """A text content block"""

    class Meta:
        icon = "edit"
        template = "blocks/text.html"

    def __init__(self, *args, **kwargs):
        kwargs["features"] = kwargs.get("features", RICH_TEXT_FEATURES)
        super().__init__(*args, **kwargs)


class UsefulLinkBlock(blocks.StructBlock):
    title = blocks.CharBlock(help_text="This will be displayed on the sidebar.")
    page = blocks.PageChooserBlock(required=False)
    url = blocks.URLBlock(required=False)

    class Meta:
        label = "Useful links"
        icon = "link"

    def clean(self, value):
        if not value.get("page") and not value.get("url"):
            raise ValidationError(
                "You must provide either a page or a URL",
                params={"page": ["You must provide either a page or a URL"]},
            )
        if value.get("page") and value.get("url"):
            raise ValidationError(
                "You must provide either a page or a URL, not both",
                params={
                    "page": ["You must provide either a page or a URL"],
                    "url": ["You must provide either a page or a URL"],
                },
            )
        return super().clean(value)

    def get_url(self, value):
        """Get the URL of the page or the URL provided"""
        if value.get("page"):
            return value["page"].url
        return value["url"]


class ImageBlock(blocks.StructBlock):
    """An image block with accessible metadata"""

    image = ImageChooserBlock()
    isdecorative = blocks.BooleanBlock(
        required=False,
        label="Is this a decorative image?",
        help_text="""
        Tick if this image is entirely decorative and does not include
        important content. This will hide the image from users using
        screen readers.
        """,
    )
    alt = blocks.CharBlock(
        required=False,
        label="Alt text",
        help_text="""
        Read out by screen readers or displayed if an image does not load
        or if images have been switched off.

        Unless this is a decorative image, it MUST have alt text that
        tells people what information the image provides, describes its
        content and function, and is specific, meaningful and concise.
        """,
    )
    caption = blocks.CharBlock(
        required=False,
        help_text="""
        Optional text displayed under the image on the page to provide
        context.
        """,
    )

    class Meta:
        icon = "image"
        template = "blocks/image.html"

    def clean(self, value):
        if value["isdecorative"]:
            errors = {}

            if value["alt"]:
                errors["alt"] = ["Decorative images cannot have alt text"]
            if value["caption"]:
                errors["caption"] = ["Decorative images cannot have a caption"]

            if errors:
                raise ValidationError(
                    "Alt or caption provided for decorative image", params=errors
                )
        elif not value["alt"]:
            raise ValidationError(
                "Alt text is missing", params={"alt": ["Image must have alt text"]}
            )
        return super().clean(value)


class ImageWithTextBlock(blocks.StructBlock):
    """An image block with text left or right of it"""

    heading = Heading3Block()
    text = TextBlock()
    image_position = blocks.ChoiceBlock(
        choices=[("left", "Left"), ("right", "Right")],
        default="left",
        help_text="Position of the image relative to the text",
    )
    image = ImageChooserBlock()
    image_description = blocks.CharBlock(
        required=False,
        help_text="""
        Optional text displayed under the image to provide context.
        """,
    )
    alt = blocks.CharBlock(
        required=False,
        label="Alt text",
        help_text="""
        Read out by screen readers or displayed if an image does not load
        or if images have been switched off.

        Unless this is a decorative image, it MUST have alt text that
        tells people what information the image provides, describes its
        content and function, and is specific, meaningful and concise.
        """,
    )

    class Meta:
        label = "Image with text"
        icon = "image"
        template = "blocks/image_with_text.html"


class MediaChooserBlock(AbstractMediaChooserBlock):
    """Media file chooser for the admin interface

    ``wagtailmedia`` is quite an incomplete and immature plugin as Wagtail
    recommends embedding external videos only. We aim to move to that model
    eventually, but in the medium term we need to replicate the basic video
    functionality present in the previous Wordpress-based Digital Workspace.

    This block is only used to allow other blocks to have a media chooser,
    and does not need to be able to render itself, hence it doesn"t implement
    ``AbstractMediaChooserBlock.render_basic()``.
    """

    def render_basic(self, value):
        pass


class InternalMediaBlock(blocks.StructBlock):
    """A video or audio player block for uploaded media files"""

    media_file = MediaChooserBlock()

    class Meta:
        label = "Video or Audio"
        icon = "media"
        template = "blocks/media.html"


class DataTableBlock(TableBlock):
    """A simple table block"""

    class Meta:
        template = "blocks/table.html"


class EmbedVideoBlock(blocks.StructBlock):
    """Only used for Video Card modals."""

    video = EmbedBlock(
        help_text="Paste a URL from Microsoft Stream or Youtube. Please "
        "use the page URL rather than the URL from the embed code."
    )  # <-- the part we need

    class Meta:
        template = "blocks/video_embed.html"
        icon = "media"
        label = "Embed Video"


class CTABlock(blocks.StructBlock):
    """Call to action section"""

    text = blocks.CharBlock(required=True, max_length=40)
    page = blocks.PageChooserBlock(required=False)
    url = blocks.URLBlock(required=False)

    class Meta:
        template = "blocks/cta.html"
        icon = "thumbtack"
        label = "CTA Button"


class PageUpdate(blocks.StructBlock):
    update_time = blocks.DateTimeBlock()
    person = PersonChooserBlock(required=False)
    note = blocks.CharBlock(required=False)

    class Meta:
        icon = "thumbtack"
        label = "CTA Button"
