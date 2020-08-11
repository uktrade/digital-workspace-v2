from datetime import datetime

from django.core.management.base import BaseCommand

from wagtail.core.models import Page

from content.models import (
    PoliciesAndGuidance,
    ToolsHome,
    NewsHome,
)


class Command(BaseCommand):
    help = "Create section homepages"

    def handle(self, *args, **options):
        home_page = Page.objects.filter(slug="home").first()
        #
        # news_home_content_type = ContentType.objects.get(app_label='content', model='newshome', )
        # tools_home_content_type = ContentType.objects.get(app_label='content', model='toolshome', )
        # policiesandguidance_content_type = ContentType.objects.get(app_label='content', model='policiesandguidance', )

        news_home = NewsHome(
            # path="news-and-views",
            # content_type=news_home_content_type,
            title="News",
            slug="news-and-views",
            live=True,
            first_published_at=datetime.now(),
        )

        home_page.add_child(instance=news_home)
        home_page.save()

        tools_home = ToolsHome(
            # path="news-and-views",
            # content_type=tools_home_content_type,
            title="Tool pages",
            slug="tools",
            live=True,
            first_published_at=datetime.now(),
        )

        home_page.add_child(instance=tools_home)
        home_page.save()

        polcies_and_guidance = PoliciesAndGuidance(
            # path="news-and-views",
            # content_type=policiesandguidance_content_type,
            title="Policies and Guidance",
            slug="policies-and-guidance",
            live=True,
            first_published_at=datetime.now(),
        )

        home_page.add_child(instance=polcies_and_guidance)
        home_page.save()
