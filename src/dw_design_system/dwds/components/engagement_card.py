from wagtail import blocks


class EngagementCardBlock(blocks.StructBlock):
    page = blocks.PageChooserBlock(page_type="content.ContentPage")

    class Meta:
        template = "dwds/components/engagement_card.html"
        icon = "doc-empty"
        label = "Engagement Card"

    def get_context(self, value, parent_context=None):
        from content.models import BlogPost
        from news.models import NewsPage

        context = parent_context or {}

        page = value.get("page")
        if not page:
            return context
        page = page.specific

        author = None
        if content_owner := getattr(page, "content_owner", None):
            author = content_owner.full_name
        elif page.owner:
            author = page.owner.get_full_name()

        context.update(
            title=page.title,
            excerpt=page.excerpt,
            author=author,
            thumbnail=getattr(page, "preview_image", None),
            date=page.published_date,
            url=page.url,
            is_highlighted=isinstance(page, NewsPage) or isinstance(page, BlogPost),
            comment_count=page.get_comment_count(),
        )

        return context

    def get_searchable_heading(self, value):
        page = value["page"]
        return page.title
