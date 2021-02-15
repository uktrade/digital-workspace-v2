import json
import logging

from django.template.defaultfilters import slugify

from import_wordpress.parser.block_content import (
    parse_into_blocks,
)
from import_wordpress.utils.helpers import (
    assign_documents,
    get_author,
    get_search_pin_exclude,
    is_archived,
    is_live,
    set_topics,
)


logger = logging.getLogger(__name__)


def populate_section_homepage(content, content_class, attachments, path):
    author = get_author(content)
    live = is_live(content["status"])

    page_home = content_class.objects.filter(slug=slugify(path)).first()

    title = content["title"]
    if not title:
        title = "NO TITLE"

    page_home.first_published_at = content["pub_date"]
    page_home.last_published_at = content["post_date"]
    page_home.title = title
    page_home.legacy_guid = content["guid"]
    page_home.legacy_path = path
    page_home.legacy_content = content["content"]
    page_home.live = live
    page_home.save()

    block_content = parse_into_blocks(
        content["content"],
        attachments,
    )

    page_home.body = json.dumps(block_content)
    set_topics(content, page_home)

    revision = page_home.save_revision(
        user=author,
        submitted_for_moderation=False,
    )
    revision.publish()
    page_home.save()

    return page_home


def get_page_path(full_path):
    parts = full_path.split("/")
    return f'{"/".join(parts[-2])}/'


# def check_slug(page_path, counter=0):
#     slug = slugify(get_page_path(page_path))
#     existing_page = Page.objects.filter(
#         slug=slug,
#     ).first()
#
#     if existing_page:
#         counter += 1
#         return check_slug(f"{page_path[:-1]}_{counter}/")
#
#     return slug


def create_page(
    page_content,
    content_class,
    parent,
    path,
    attachments,
):
    logger.info(f"Processing path: {path}")
    author = get_author(page_content)
    live = is_live(page_content["status"])

    title = page_content["title"]

    if live:
        live = is_archived(title)

    if not title:
        title = "NO TITLE"

    pinned, exclude = get_search_pin_exclude(page_content)

    content_page = content_class(
        first_published_at=page_content["pub_date"],
        last_published_at=page_content["post_date"],
        title=title,
        slug=slugify(get_page_path(path)),
        legacy_path=path,
        legacy_guid=page_content["guid"],
        legacy_content=page_content["content"],
        live=live,
        pinned_phrases=pinned,
        excluded_phrases=exclude,
    )

    if page_content["excerpt"]:
        content_page.excerpt = page_content["excerpt"]

    if "redirect_url" in page_content:
        content_page.redirect_url = page_content["redirect_url"]

    parent.add_child(instance=content_page)
    parent.save()

    if page_content["content"]:
        block_content = parse_into_blocks(
            page_content["content"],
            attachments,
        )

        content_page.body = json.dumps(block_content)

    set_topics(page_content, content_page)

    assign_documents(content_page, page_content, attachments)

    content_page.save()

    if live:
        revision = content_page.save_revision(
            user=author,
            submitted_for_moderation=False,
        )
        revision.publish()
        content_page.save()

    return content_page
