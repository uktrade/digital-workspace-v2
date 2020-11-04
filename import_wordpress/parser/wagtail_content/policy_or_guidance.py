import json

from django.template.defaultfilters import slugify

from wagtail.contrib.redirects.models import Redirect

from import_wordpress.parser.block_content import (
    parse_into_blocks,
)
from import_wordpress.utils.helpers import (
    get_author,
    get_slug,
    is_live,
    set_topics,
)

from working_at_dit.models import (
    PoliciesHome,
    GuidanceHome,
    Guidance,
    Policy,
)


def create_policy_or_guidance(policy_or_guidance, attachments):
    author = get_author(policy_or_guidance)

    live = is_live(policy_or_guidance["status"])

    if not live:
        return

    link = policy_or_guidance["link"].replace(
        "/working-at-dit/policies-and-guidance",
        "",
    )

    path = get_slug(link)

    is_policy = policy_or_guidance["policy_or_guidance"] == "policy"

    if is_policy:
        home = PoliciesHome.objects.all().first()
    else:
        home = GuidanceHome.objects.all().first()

    if is_policy:
        content_page = Policy(
            first_published_at=policy_or_guidance["pub_date"],
            last_published_at=policy_or_guidance["post_date"],
            title=policy_or_guidance["title"],
            slug=slugify(path),
            legacy_guid=policy_or_guidance["guid"],
            legacy_content=policy_or_guidance["content"],
            live=live,
        )
    else:
        content_page = Guidance(
            first_published_at=policy_or_guidance["pub_date"],
            last_published_at=policy_or_guidance["post_date"],
            title=policy_or_guidance["title"],
            slug=slugify(path),
            legacy_guid=policy_or_guidance["guid"],
            legacy_content=policy_or_guidance["content"],
            live=live,
        )

    home.add_child(instance=content_page)
    home.save()

    block_content = parse_into_blocks(
        policy_or_guidance["content"],
        attachments,
    )

    content_page.body = json.dumps(block_content)
    set_topics(policy_or_guidance, content_page)

    revision = content_page.save_revision(
        user=author,
        submitted_for_moderation=False,
    )
    revision.publish()
    content_page.save()

    # Create redirect
    if live:
        Redirect.objects.create(
            old_path=f'/working-at-dit/policies-and-guidance{link[:-1]}',
            redirect_page=content_page,
        )
