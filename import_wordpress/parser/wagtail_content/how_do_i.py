from django.template.defaultfilters import slugify

from import_wordpress.parser.wagtail_content.page import WPPage
from working_at_dit.models import HowDoI, HowDoIHome


class HowDoIPage(WPPage):
    def get_parent(self):
        return HowDoIHome.objects.filter(slug="how-do-i").first()

    def create(self):
        path = self.get_slug(
            self.page_content["link"].replace(
                "/working-at-dit/how-do-i",
                "",
            )
        )

        self.wagtail_page = HowDoI(
            first_published_at=self.page_content["pub_date"],
            last_published_at=self.page_content["post_date"],
            title=self.title,
            slug=slugify(path),
            legacy_guid=self.page_content["guid"],
            legacy_content=self.page_content["content"],
            live=self.live,
            pinned_phrases=self.pinned,
            excluded_phrases=self.exclude,
        )

        self.post_create()
