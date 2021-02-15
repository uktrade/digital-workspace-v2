import json
import logging

from django.contrib.auth import get_user_model
from django.template.defaultfilters import slugify
from wagtail.core.models import Page

from import_wordpress.parser.block_content import (
    parse_into_blocks,
)
from import_wordpress.utils.helpers import (
    assign_documents,
    get_author,
    get_preview_image,
    get_search_pin_exclude,
    get_slug,
    is_live,
)
from news.models import (
    Comment,
    NewsCategory,
    NewsHome,
    NewsPage,
    NewsPageNewsCategory,
)
from working_at_dit.models import PageTopic, Topic


logger = logging.getLogger(__name__)


UserModel = get_user_model()

home_page = Page.objects.filter(slug="home").first()

processed_categories = []


def create_news_home(post_date):
    news_home = NewsHome(
        # path="news-and-views",
        title="All News",
        slug="news-and-views",
        live=True,
        first_published_at=post_date,
        show_in_menus=True,
    )

    home_page.add_child(instance=news_home)
    home_page.save()
    return NewsHome.objects.all().first()


def create_comment(comment, content_page, comments):
    try:
        # Check to see if comment exists (could have been made as a parent)
        existing_comment = Comment.objects.filter(
            legacy_id=int(comment["legacy_id"]),
        ).first()

        if existing_comment:
            return existing_comment

        #  Check for parent
        parent_comment = None

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

        # assert author is not None
        # TODO - think about implications
        if author is None:
            return

        return Comment.objects.create(
            legacy_id=int(comment["legacy_id"]),
            author=author,
            news_page=content_page,
            content=comment["content"],
            parent=parent_comment,
        )
    except Exception:
        logger.error("Exception when creating comment", exc_info=True)


def create_news_page(
    news_item,
    attachments,
):
    if not news_item["title"]:
        return

    live = is_live(news_item["status"])

    if not live:
        return

    # check for existence of parent news page
    news_home = Page.objects.filter(slug="news-and-views").first()

    path = get_slug(
        news_item["link"].replace(
            "/news-and-views",
            "",
        )
    )

    author = get_author(news_item)

    pinned, exclude = get_search_pin_exclude(news_item)

    excerpt = None

    if "excerpt" in news_item:
        excerpt = news_item["excerpt"]

    if "preview_image_id" in news_item:
        preview_image = get_preview_image(
            attachments,
            news_item["preview_image_id"],
        )

        content_page = NewsPage(
            first_published_at=news_item["pub_date"],
            last_published_at=news_item["post_date"],
            title=news_item["title"],
            slug=slugify(path),
            legacy_guid=news_item["guid"],
            legacy_content=news_item["content"],
            live=live,
            preview_image=preview_image,
            excerpt=excerpt,
            pinned_phrases=pinned,
            excluded_phrases=exclude,
        )
    else:
        content_page = NewsPage(
            first_published_at=news_item["pub_date"],
            last_published_at=news_item["post_date"],
            title=news_item["title"],
            slug=slugify(path),
            legacy_guid=news_item["guid"],
            legacy_content=news_item["content"],
            live=live,
            excerpt=excerpt,
            pinned_phrases=pinned,
            excluded_phrases=exclude,
        )

    news_home.add_child(instance=content_page)
    news_home.save()

    page_news_categories = []

    # Set categories
    if "categories" in news_item:
        for category in news_item["categories"]:
            if category not in processed_categories:
                news_category = NewsCategory(
                    category=category,
                )
                news_category.save()
                processed_categories.append(category)
            else:
                news_category = NewsCategory.objects.filter(
                    category=category,
                ).first()

            page_news_categories.append(news_category)

    # Comments
    for comment in news_item["comments"]:
        create_comment(
            comment,
            content_page,
            news_item["comments"],
        )

    block_content = parse_into_blocks(
        news_item["content"],
        attachments,
    )

    content_page.body = json.dumps(block_content)

    for news_category in page_news_categories:
        NewsPageNewsCategory.objects.create(
            news_category=news_category,
            news_page=content_page,
        )

    # Set relationship with Topic pages
    if "topics" in news_item:
        for wp_topic in news_item["topics"]:
            topic = Topic.objects.filter(title=wp_topic["name"]).first()

            if not topic:
                logger.warning(
                    f"COULD NOT FIND TOPIC: '{topic}'",
                )
                continue

            PageTopic.objects.get_or_create(
                topic=topic,
                page=content_page,
            )
            content_page.save()

    content_page.save()

    assign_documents(content_page, news_item, attachments)

    revision = content_page.save_revision(
        user=author,
        submitted_for_moderation=False,
    )
    revision.publish()
    content_page.save()
