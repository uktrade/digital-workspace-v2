from django.template.defaultfilters import slugify
from wagtail.contrib.redirects.models import Redirect
from wagtail.core.models import Page

from content.models import Theme
from import_wordpress.parser.wagtail_content.page import WPPage
from working_at_dit.models import Topic, TopicTheme


class TopicPage(WPPage):
    def get_parent(self):
        return Page.objects.filter(slug="topics").first()

    def create(self):
        path = self.get_slug(
            self.page_content["link"].replace(
                "/working-at-dit",
                "",
            )
        )

        wp_themes = [t["name"] for t in self.page_content["themes"]]
        themes = Theme.objects.filter(title__in=wp_themes).all()

        self.wagtail_page = Topic(
            first_published_at=self.page_content["pub_date"],
            last_published_at=self.page_content["post_date"],
            title=self.title,
            slug=slugify(path),
            legacy_guid=self.page_content["guid"],
            legacy_content=self.page_content["content"],
            live=self.live,
            pinned_phrases=self.pinned,
            excluded_phrases=self.excluded,
        )

        self.post_create()

        for theme in themes:
            TopicTheme.objects.get_or_create(
                theme=theme,
                topic=self.wagtail_page,
            )

        if self.live:
            # Create redirect
            Redirect.objects.create(
                old_path=self.page_content["link"][:-1],
                redirect_page=self.wagtail_page,
            )
