import json


from django.template.defaultfilters import slugify

from import_wordpress.parser.block_content import (
    parse_into_blocks,
)
from import_wordpress.utils.helpers import (
    get_author,
    is_live,
    set_topics,
)


def populate_homepage(content, content_class, attachments, page_type):
    author = get_author(content)
    live = is_live(content["status"])

    page_home = content_class.objects.filter(slug=page_type).first()

    page_home.first_published_at = content["pub_date"]
    page_home.last_published_at = content["post_date"]
    page_home.title = content["title"]
    page_home.legacy_guid = content["guid"]
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


def create_page(page_content, content_class, parent, path, attachments):
    author = get_author(page_content)
    live = is_live(page_content["status"])

    content_page = content_class(
        first_published_at=page_content["pub_date"],
        last_published_at=page_content["post_date"],
        title=page_content["title"],
        slug=slugify(path),
        legacy_guid=page_content["guid"],
        legacy_content=page_content["content"],
        live=live,
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

    revision = content_page.save_revision(
        user=author,
        submitted_for_moderation=False,
    )
    revision.publish()
    content_page.save()
