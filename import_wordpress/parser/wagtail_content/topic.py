import json

from django.template.defaultfilters import slugify
from wagtail.contrib.redirects.models import Redirect
from wagtail.core.models import Page

from content.models import Theme
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
)
from working_at_dit.models import Topic, TopicTheme


def create_topic(topic, attachments):
    author = get_author(topic)
    live = is_live(topic["status"])

    if live:
        live = is_archived(topic["title"])

    path = get_slug(
        topic["link"].replace(
            "/working-at-dit",
            "",
        )
    )

    topic_home = Page.objects.filter(slug="topics").first()

    wp_themes = [t["name"] for t in topic["themes"]]

    themes = Theme.objects.filter(title__in=wp_themes).all()

    pinned, exclude = get_search_pin_exclude(topic)

    topic_page = Topic(
        first_published_at=topic["pub_date"],
        last_published_at=topic["post_date"],
        title=topic["title"],
        slug=slugify(path),
        legacy_guid=topic["guid"],
        legacy_content=topic["content"],
        live=live,
        pinned_phrases=pinned,
        excluded_phrases=exclude,
    )

    topic_home.add_child(instance=topic_page)
    topic_home.save()

    block_content = parse_into_blocks(
        topic["content"],
        attachments,
    )

    topic_page.body = json.dumps(block_content)

    for theme in themes:
        TopicTheme.objects.get_or_create(
            theme=theme,
            topic=topic_page,
        )

    assign_documents(topic_page, topic, attachments)

    topic_page.save()

    if live:
        revision = topic_page.save_revision(
            user=author,
            submitted_for_moderation=False,
        )
        revision.publish()
        topic_page.save()

        # Create redirect
        Redirect.objects.create(
            old_path=topic["link"][:-1],
            redirect_page=topic_page,
        )
