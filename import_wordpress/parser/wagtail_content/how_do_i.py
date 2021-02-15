import json

from django.template.defaultfilters import slugify

from import_wordpress.parser.block_content import (
    parse_into_blocks,
)
from import_wordpress.utils.helpers import (
    assign_documents,
    get_author,
    get_search_pin_exclude,
    get_slug,
    is_archived,
    is_live,
    set_topics,
)
from working_at_dit.models import HowDoI, HowDoIHome


def create_how_do_i(how_do_i, attachments):
    author = get_author(how_do_i)
    live = is_live(how_do_i["status"])

    path = get_slug(
        how_do_i["link"].replace(
            "/working-at-dit/how-do-i",
            "",
        )
    )

    how_do_i_home = HowDoIHome.objects.filter(slug="how-do-i").first()

    title = how_do_i["title"]

    if live:
        live = is_archived(title)

    if not title:
        title = "NO TITLE"

    pinned, exclude = get_search_pin_exclude(how_do_i)

    content_page = HowDoI(
        first_published_at=how_do_i["pub_date"],
        last_published_at=how_do_i["post_date"],
        title=title,
        slug=slugify(path),
        legacy_guid=how_do_i["guid"],
        legacy_content=how_do_i["content"],
        live=live,
        pinned_phrases=pinned,
        excluded_phrases=exclude,
    )

    how_do_i_home.add_child(instance=content_page)
    how_do_i_home.save()

    block_content = parse_into_blocks(
        how_do_i["content"],
        attachments,
    )

    content_page.body = json.dumps(block_content)
    set_topics(how_do_i, content_page)

    assign_documents(content_page, how_do_i, attachments)

    content_page.save()

    if live:
        revision = content_page.save_revision(
            user=author,
            submitted_for_moderation=False,
        )
        revision.publish()
        content_page.save()
