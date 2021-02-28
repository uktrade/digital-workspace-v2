from django.template.defaultfilters import slugify
from wagtail.contrib.redirects.models import Redirect

from import_wordpress.parser.wagtail_content.page import WPPage
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


class PolicyOrGuidancePage(WPPage):
    def get_parent(self):
        if self.page_content["policy_or_guidance"] == "policy":
            return PoliciesHome.objects.all().first()
        else:
            return GuidanceHome.objects.all().first()

    def create(self):
        slug = self.page_content["link"].replace(
            "/working-at-dit/policies-and-guidance",
            "",
        )

        if self.page_content["policy_or_guidance"] == "policy":
            self.wagtail_page = Policy(
                first_published_at=self.page_content["pub_date"],
                last_published_at=self.page_content["post_date"],
                title=self.title,
                slug=slugify(slug),
                legacy_guid=self.page_content["guid"],
                legacy_content=self.page_content["content"],
                live=self.live,
                pinned_phrases=self.pinned,
                excluded_phrases=self.excluded,
            )
        else:
            self.wagtail_page = Guidance(
                first_published_at=self.page_content["pub_date"],
                last_published_at=self.page_content["post_date"],
                title=self.title,
                slug=slugify(slug),
                legacy_guid=self.page_content["guid"],
                legacy_content=self.page_content["content"],
                live=self.live,
                pinned_phrases=self.pinned,
                excluded_phrases=self.excluded,
            )

        self.post_create()

        # Create redirect
        if self.live:
            link = self.page_content["link"].replace(
                "/working-at-dit/policies-and-guidance",
                "",
            )

            redirect_url = link[:-1]
            if link in orphan_policy or link in orphan_guidance:
                redirect_url = link

            Redirect.objects.create(
                old_path=f"/working-at-dit/policies-and-guidance{redirect_url}",
                redirect_page=self.wagtail_page,
            )

            revision = self.wagtail_page.save_revision(
                user=self.author,
                submitted_for_moderation=False,
                log_action=False,
            )
            revision.publish()
            revision.created_at = self.page_content["post_date"]
            revision.save()
            self.wagtail_page.last_published_at = self.page_content["post_date"]
            self.wagtail_page.first_published_at = self.page_content["post_date"]
            self.wagtail_page.latest_revision_created_at = self.page_content["post_date"]
            self.wagtail_page.save()
