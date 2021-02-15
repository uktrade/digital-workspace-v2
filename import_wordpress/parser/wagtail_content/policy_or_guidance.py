import json

from django.template.defaultfilters import slugify
from wagtail.contrib.redirects.models import Redirect

from import_wordpress.parser.block_content import (
    parse_into_blocks,
)
from import_wordpress.utils.helpers import (
    assign_documents,
    get_author,
    get_search_pin_exclude,
    get_slug,
    is_live,
    set_topics,
)
from import_wordpress.utils.orphans import (
    orphan_guidance,
    orphan_policy,
)
from working_at_dit.models import (
    Guidance,
    GuidanceHome,
    PoliciesHome,
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

    pinned, exclude = get_search_pin_exclude(policy_or_guidance)

    if is_policy:
        content_page = Policy(
            first_published_at=policy_or_guidance["pub_date"],
            last_published_at=policy_or_guidance["post_date"],
            title=policy_or_guidance["title"],
            slug=slugify(path),
            legacy_guid=policy_or_guidance["guid"],
            legacy_content=policy_or_guidance["content"],
            live=live,
            pinned_phrases=pinned,
            excluded_phrases=exclude,
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
            pinned_phrases=pinned,
            excluded_phrases=exclude,
        )

    home.add_child(instance=content_page)
    home.save()

    block_content = parse_into_blocks(
        policy_or_guidance["content"],
        attachments,
    )

    content_page.body = json.dumps(block_content)
    set_topics(policy_or_guidance, content_page)

    assign_documents(content_page, policy_or_guidance, attachments)

    content_page.save()

    # Create redirect
    if live:
        redirect_url = link[:-1]
        if link in orphan_policy or link in orphan_guidance:
            redirect_url = link

        Redirect.objects.create(
            old_path=f"/working-at-dit/policies-and-guidance{redirect_url}",
            redirect_page=content_page,
        )

        revision = content_page.save_revision(
            user=author,
            submitted_for_moderation=False,
        )
        revision.publish()
        content_page.save()
