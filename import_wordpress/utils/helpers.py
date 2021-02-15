import json
import logging
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth import get_user_model
from wagtail.core.models import Page
from wagtail.documents.models import Document as WagtailDocument
from wagtail.images.models import Image as WagtailImage

from content.models import (
    SearchKeywordOrPhrase,
)
from working_at_dit.models import PageTopic, Topic


logger = logging.getLogger(__name__)


UserModel = get_user_model()


def is_live(status):
    if status == "publish":
        return True

    return False


def get_preview_image(attachments, attachment_id):
    try:
        attachment_url = attachments[attachment_id]["attachment_url"]
        parsed = urlparse(attachment_url)

        return WagtailImage.objects.filter(file=parsed.path[1:]).first()
    except Exception:
        logger.error("Exception when calling 'get_preview_image'", exc_info=True)
        return None


def get_slug(slug, counter=1):
    page_with_slug = Page.objects.filter(slug=slug).first()

    if page_with_slug:
        return get_slug(f"{page_with_slug}-{counter}", (counter + 1))

    return slug


def get_author(item):
    domains = [
        "trade.gov.uk",
        "digital.trade.gov.uk",
        "trade.gsi.gov.uk",
    ]

    author = None

    # Exceptions to general pattern
    if item["creator"] == settings.AUTHOR_TO_BE_SUBSTITUTED:
        item["creator"] = settings.AUTHOR_SUBSTITUTED

    for domain in domains:
        author_email = f'{item["creator"].lower()}@{domain}'
        author = UserModel.objects.filter(email=author_email).first()

        if author:
            break

    if not author:
        logger.warning(f"Could not find author: '{item['creator']}'")
        author = UserModel.objects.filter(email="connect@digital.trade.gov.uk").first()

    return author


def set_topics(content, page):
    # Set relationship with Topic pages
    if "topics" in content:
        for wp_topic in content["topics"]:
            topic = Topic.objects.filter(title=wp_topic["name"]).first()

            if not topic:  #  Some topics have been archvied
                logger.warning(f'SKIPPED TOPIC: "{wp_topic["name"]}" for page "{page}"')
                continue

            PageTopic.objects.get_or_create(
                topic=topic,
                page=page,
            )
            page.save()


def get_keyword_or_phrase(value):
    keyword_or_phrase = SearchKeywordOrPhrase.objects.filter(
        keyword_or_phrase=value,
    ).first()

    if not keyword_or_phrase:
        keyword_or_phrase = SearchKeywordOrPhrase.objects.create(
            keyword_or_phrase=value,
        )

    return keyword_or_phrase


def assign_documents(content_page, item, attachments):
    blocks = []
    for document_file_post_id in item["document_files"]:
        for _key, value in attachments.items():
            if value["post_id"] == document_file_post_id:
                title = value["content"]

                attachment_url = value["attachment_url"]
                parsed = urlparse(attachment_url)
                s3_path = parsed.path[1:]

                document = WagtailDocument.objects.filter(
                    file=s3_path,
                ).first()

                if not document:
                    logger.warning(f"COULD NOT FIND DOCUMENT: '{s3_path}'")
                else:
                    if title:
                        document.title = title
                        document.save()

                    logger.info(f"ASSIGNING DOCUMENT: {s3_path}")

                    blocks.append(
                        {"type": "footer_document_list_item", "value": document.id}
                    )

    content_page.footer_documents = json.dumps(blocks)


ARCHIVE_STR_LIST = (
    "[archived]",
    "[ARCHIVED]",
    "[ARCHIVE]",
    "Archive - ",
)


def is_archived(title):
    for archive_str in ARCHIVE_STR_LIST:
        if title in archive_str:
            return False

    return True


def get_search_pin_exclude(item):
    pinned_str = ""
    for pinned in item["search_pinned"]:
        pinned_str = pinned_str + f"{pinned}, "

    exclude_str = ""
    for excluded in item["search_excluded"]:
        exclude_str = exclude_str + f"{excluded}, "

    return pinned_str, exclude_str
