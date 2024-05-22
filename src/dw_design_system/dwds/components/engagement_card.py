from wagtail import blocks


class EngagementCardBlock(blocks.StructBlock):
    page = blocks.PageChooserBlock(page_type="content.ContentPage")

    class Meta:
        template = "dwds/components/engagement_card.html"
        icon = "doc-empty"
        label = "Engagement Card"

    def get_context(self, value, parent_context=None):
        from news.models import NewsPage

        context = parent_context or {}

        page = value.get("page")
        if not page:
            return context
        page = page.specific

        author = page.owner.get_full_name()
        if content_owner := getattr(page, "content_owner", None):
            author = content_owner.full_name

        context.update(
            title=page.title,
            author=author,
            thumbnail=getattr(page, "preview_image", None),
            date=page.published_date,
            url=page.url,
            is_news=isinstance(page, NewsPage),
        )

        return context
