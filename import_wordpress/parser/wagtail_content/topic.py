from django.template.defaultfilters import slugify

from wagtail.core.models import Page


from import_wordpress.parser.process_content import (
    set_content,
)
from import_wordpress.utils.helpers import (
    get_author,
    get_slug,
    is_live,
)

from working_at_dit.models import Topic


def create_topic(topic, attachments):
    author = get_author(topic)
    live = is_live(topic["status"])

    path = get_slug(
        topic["link"].replace(
            "/working-at-dit",
            "",
        )
    )

    topic_home = Page.objects.filter(slug="topics").first()

    topic_page = Topic(
        first_published_at=topic["pub_date"],
        last_published_at=topic["post_date"],
        title=topic["title"],
        slug=slugify(path),
        legacy_guid=topic["guid"],
        legacy_content=topic["content"],
        live=live,
    )

    topic_home.add_child(instance=topic_page)
    topic_home.save()

    set_content(
        author,
        topic["content"],
        topic_page,
        attachments
    )
