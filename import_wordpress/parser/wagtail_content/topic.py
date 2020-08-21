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

from content.models import Theme

from working_at_dit.models import Topic, TopicTheme


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

    wp_themes = [t["nice_name"] for t in topic["themes"]]

    themes = Theme.objects.filter(
        theme__in=wp_themes
    ).all()

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

    for theme in themes:
        TopicTheme.objects.get_or_create(
            theme__name=theme,
            topic=topic_page,
        )

    revision = topic_page.save_revision(
        user=author,
        submitted_for_moderation=False,
    )
    revision.publish()
    topic_page.save()
