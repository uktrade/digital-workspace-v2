from wagtail import blocks

class CTACardBlock(blocks.StructBlock):
    """Call to action section"""
    title = blocks.CharBlock(required=True, max_length=80)
    description = blocks.CharBlock(required=False, max_length=80)
    page = blocks.PageChooserBlock(required=False)
    url = blocks.URLBlock(required=False)

    class Meta:
        template = "dwds/components/cta_card.html"
        icon = "info-circle"
        label = "CTA Card"

    def get_context(self, value, parent_context=None):
        context = parent_context or {}
        url = ""

        if(value["page"]):
            url = value["page"].url
        else:
            url = value["url"]

        context.update(
            title=value["title"],
            description=value["description"],
            url=url,
        )
        return context