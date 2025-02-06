from wagtail import blocks


class EngagementCardBlock(blocks.StructBlock):
    page = blocks.PageChooserBlock(page_type="content.ContentPage")

    class Meta:
        template = "dwds/components/engagement.html"
        icon = "doc-empty"
        label = "Engagement Card"

    def get_context(self, value, parent_context=None):
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
        )

        if isinstance(page, NewsPage):
            news_page = (
                NewsPage.objects.annotate_with_comment_count()
                .annotate_with_reaction_count()
                .get(pk=page.pk)
            )
            context.update(comment_count=news_page.comment_count)
        return context

    def get_searchable_heading(self, value):
        page = value["page"]
        return page.title
