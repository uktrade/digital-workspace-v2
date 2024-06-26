from django.core.exceptions import ValidationError
from wagtail import blocks

from content import blocks as content_blocks


class CTACardBlock(blocks.StructBlock):
    """Call to action section"""

    title = content_blocks.HeadingBlock(required=True, max_length=30)
    description = blocks.CharBlock(required=False, max_length=70)
    page = blocks.PageChooserBlock(required=False)
    url = blocks.URLBlock(required=False)

    class Meta:
        template = "dwds/components/cta_card.html"
        icon = "info-circle"
        label = "CTA Card"

    def clean(self, value):
        errors = {}
        if value["page"] and value["url"]:
            raise ValidationError(
                "CTA card requires either a page or url, not both", params=errors
            )
        if not value["page"] and not value["url"]:
            raise ValidationError(
                "CTA card requires either a page or url", params=errors
            )

        return super().clean(value)

    def get_context(self, value, parent_context=None):
        context = parent_context or {}
        url = ""

        if value["page"]:
            url = value["page"].get_url()
        else:
            url = value["url"]

        context.update(
            title=value["title"],
            description=value["description"],
            url=url,
        )
        return context

    def get_searchable_heading(self, value):
        title = value["title"]
        page = value["page"]
        return title or page.title
