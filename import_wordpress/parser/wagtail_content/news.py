import logging

from django.contrib.auth import get_user_model
from django.template.defaultfilters import slugify
from wagtail.core.models import Page

from import_wordpress.parser.wagtail_content.page import WPPage
from news.models import (
    Comment,
    NewsCategory,
    NewsPage,
    NewsPageNewsCategory,
)


logger = logging.getLogger(__name__)


UserModel = get_user_model()


def create_comment(comment, content_page, comments):
    try:
        # Check to see if comment exists (could have been made as a parent)
        existing_comment = Comment.objects.filter(
            legacy_id=int(comment["legacy_id"]),
        ).first()

        if existing_comment:
            return existing_comment

        parent_comment = None

        #  Check for parent
        if comment["parent_id"] != "0":
            parent_comment = Comment.objects.filter(
                legacy_id=int(comment["parent_id"]),
            ).first()

            if not parent_comment:
                # Get parent comment
                for c in comments:
                    if "parent" not in comment:
                        return

                    if c["legacy_id"] == comment["parent"]:
                        parent_comment = create_comment(c, content_page, comments)

        author = UserModel.objects.filter(email=comment["author_email"]).first()

        logger.info(
            f"Creating comment '{comment['content']}' by {comment['author_name']}"
        )

        return Comment.objects.create(
            legacy_id=int(comment["legacy_id"]),
            posted_date=comment["comment_date"],
            author=author,
            legacy_author_email=comment["author_email"],
            legacy_author_name=comment["author_name"],
            news_page=content_page,
            content=comment["content"],
            parent=parent_comment,
        )
    except Exception:
        logger.error("Exception when creating comment", exc_info=True)


class WagtailNewsPage(WPPage):
    def get_parent(self):
        return Page.objects.filter(slug="news-and-views").first()

    def create(self):
        slug = self.get_slug(
            self.page_content["link"].replace(
                "/news-and-views",
                "",
            )
        )

        self.wagtail_page = NewsPage(
            first_published_at=self.page_content["pub_date"],
            last_published_at=self.page_content["post_date"],
            title=self.title,
            slug=slugify(slug),
            legacy_guid=self.page_content["guid"],
            legacy_content=self.page_content["content"],
            live=self.live,
            pinned_phrases=self.pinned,
            excluded_phrases=self.excluded,
        )

        if (
            "preview_image_id" in self.page_content
            and self.page_content["preview_image_id"]  # noqa W504
        ):
            preview_image = self.get_preview_image(
                self.page_content["preview_image_id"],
            )
            self.wagtail_page.preview_image = preview_image

        page_news_categories = []

        # Set categories
        if "categories" in self.page_content:
            for category in self.page_content["categories"]:
                news_category = NewsCategory.objects.filter(
                    category=category,
                ).first()

                if not news_category:
                    news_category = NewsCategory(
                        category=category,
                    )
                    news_category.save()

                page_news_categories.append(news_category)

        self.post_create()

        # Comments
        for comment in self.page_content["comments"]:
            create_comment(
                comment,
                self.wagtail_page,
                self.page_content["comments"],
            )

        for news_category in page_news_categories:
            NewsPageNewsCategory.objects.create(
                news_category=news_category,
                news_page=self.wagtail_page,
            )

        revision = self.wagtail_page.save_revision(
            user=self.author,
            submitted_for_moderation=False,
            log_action=False,
        )
        revision.publish()
        revision.created_at = self.page_content["post_date"]
        revision.save()
        self.wagtail_page.last_published_at = self.page_content["post_date"]
        self.wagtail_page.first_published_at = self.page_content["post_date"]
        self.wagtail_page.latest_revision_created_at = self.page_content["post_date"]
        self.wagtail_page.save()
