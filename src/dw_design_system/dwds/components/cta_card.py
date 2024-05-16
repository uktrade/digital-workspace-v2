from wagtail import blocks

class CTACardBlock(blocks.StructBlock):
    """Call to action section"""
    title = blocks.CharBlock(required=True, max_length=80)
    text = blocks.CharBlock(required=True, max_length=80)
    page = blocks.PageChooserBlock(required=False)
    url = blocks.URLBlock(required=False)

    class Meta:
        template = "dwds/components/cta_card.html"
        icon = "thumbtack"
        label = "CTA Card"