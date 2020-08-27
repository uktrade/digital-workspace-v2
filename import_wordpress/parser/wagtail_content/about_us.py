import json

from django.template.defaultfilters import slugify

from wagtail.core.models import Page

from import_wordpress.parser.block_content import (
    parse_into_blocks,
)
from import_wordpress.utils.helpers import (
    get_author,
    get_slug,
    is_live,
    set_topics,
)

from about_us.models import AboutUsHome, AboutUs


def populate_about_us_home(content, attachments):
    author = get_author(content)
    live = is_live(content["status"])

    about_us_home = AboutUsHome.objects.filter(slug="about-us").first()

    about_us_home.first_published_at = content["pub_date"]
    about_us_home.last_published_at = content["post_date"]
    about_us_home.title = content["title"]
    about_us_home.legacy_guid = content["guid"]
    about_us_home.legacy_content = content["content"]
    about_us_home.live = live
    about_us_home.save()

    block_content = parse_into_blocks(
        content["content"],
        attachments,
    )

    about_us_home.body = json.dumps(block_content)
    set_topics(content, about_us_home)

    revision = about_us_home.save_revision(
        user=author,
        submitted_for_moderation=False,
    )
    revision.publish()
    about_us_home.save()


def create_about_us(about_us, parent, path, attachments):
    author = get_author(about_us)
    live = is_live(about_us["status"])

    print("path", path)

    content_page = AboutUs(
        first_published_at=about_us["pub_date"],
        last_published_at=about_us["post_date"],
        title=about_us["title"],
        slug=slugify(path),
        legacy_guid=about_us["guid"],
        legacy_content=about_us["content"],
        live=live,
    )

    parent.add_child(instance=content_page)
    parent.save()

    block_content = parse_into_blocks(
        about_us["content"],
        attachments,
    )

    content_page.body = json.dumps(block_content)
    set_topics(about_us, content_page)

    revision = content_page.save_revision(
        user=author,
        submitted_for_moderation=False,
    )
    revision.publish()
    content_page.save()
