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
    image_alt = blocks.CharBlock(
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


class PersonBanner(blocks.StructBlock):
    person = PersonChooserBlock(required=False)
    person_role_id = blocks.ChoiceBlock(choices=[], required=False)
    person_name = blocks.CharBlock(required=False)
    person_role = blocks.CharBlock(required=False)
    person_image = ImageChooserBlock(
        required=False, help_text="This image should be square"
    )
    secondary_image = ImageChooserBlock(required=False)

    class Meta:
        template = "dwds/components/person_banner.html"
        icon = "user"
        label = "Person Banner"

    def clean(self, value):
        if value["person"] and (
            value["person_name"] or value["person_role"] or value["person_image"]
        ):
            raise ValidationError(
                "Either choose a person or enter the details manually."
            )
        if value["person"] and value["person"].roles.exists():
            if not value["person_role_id"]:
                raise ValidationError("A person role should always be provided.")

        return super().clean(value)

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        context.update(secondary_image=value["secondary_image"])
        if value["person"]:
            context.update(
                person_name=value["person"].full_name,
                person_image_url=(
                    value["person"].photo.url if value["person"].photo else None
                ),
            )
            if person_role := value["person"].roles.first():
                context.update(person_role=person_role.job_title)
        else:
            context.update(
                person_name=value["person_name"],
                person_role=value["person_role"],
                person_image=value["person_image"],
            )
        return context


class QuoteBlock(blocks.StructBlock):
    quote = blocks.CharBlock()
    quote_theme = blocks.ChoiceBlock(
        choices=[("light", "Light"), ("dark", "Dark")],
        default="true",
        help_text="Colour of the background. This can either be light grey or dark blue",
    )
    source = PersonChooserBlock(required=False)
    source_role_id = blocks.ChoiceBlock(choices=[], required=False)
    source_name = blocks.CharBlock(required=False)
    source_role = blocks.CharBlock(required=False)
    source_team = blocks.CharBlock(required=False)
    source_image = ImageChooserBlock(
        required=False, help_text="This image should be square"
    )

    class Meta:
        template = "dwds/components/quote.html"
        icon = "openquote"
        label = "Quote"

    def clean(self, value):
        if value["source"] and (
            value["source_name"]
            or value["source_role"]
            or value["source_team"]
            or value["source_image"]
        ):
            raise ValidationError(
                "Either choose a source or enter the details manually."
            )
        if value["source"] and value["source"].roles.exists():
            if not value["source_role_id"]:
                raise ValidationError("A source role should always be provided.")
        return super().clean(value)

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        context.update(quote=value["quote"], highlight=True)
        if value["quote_theme"] == "light":
            context.update(highlight=False)
        if value["source"]:
            context.update(
                source_name=value["source"].full_name,
                source_url=value["source"].get_absolute_url(),
                source_image_url=(
                    value["source"].photo.url if value["source"].photo else None
                ),
            )
            if source_role := value["source"].roles.first():
                context.update(
                    source_role=source_role.job_title,
                    source_team_name=source_role.team.name,
                    source_team_url=source_role.team.get_absolute_url(),
                )
        else:
            context.update(
                source_name=value["source_name"],
                source_role=value["source_role"],
                source_team_name=value["source_team"],
                source_image=value["source_image"],
            )
        return context
