from wagtail import blocks

from content.utils import truncate_words_and_chars


class OneUpCardBlock(blocks.StructBlock):
    page = blocks.PageChooserBlock(page_type="content.ContentPage")

    class Meta:
        template = "dwds/components/one_up_card.html"
        icon = "doc-empty"
        label = "One up Card"

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
            title=truncate_words_and_chars(
                page.title, words=7, chars=30, include_elipsis=True
            ),
            excerpt=truncate_words_and_chars(
                page.excerpt, words=200, chars=200, include_elipsis=True
            ),
            author=author,
            thumbnail=getattr(page, "preview_image", None),
            date=page.published_date,
            url=page.url,
            is_highlighted=isinstance(page, NewsPage) or isinstance(page, BlogPost),
        )

        return context
