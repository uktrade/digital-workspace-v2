from wagtail import blocks


class CTABlock(blocks.StructBlock):
    """Call to action section"""

    text = blocks.CharBlock(required=True, max_length=40)
    page = blocks.PageChooserBlock(required=False)
    url = blocks.URLBlock(required=False)

    class Meta:
        template = "dwds/components/cta.html"
        icon = "thumbtack"
        label = "CTA"
