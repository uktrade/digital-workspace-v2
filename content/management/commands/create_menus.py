from datetime import datetime

from django.core.management.base import BaseCommand

from wagtail.core.models import Page

from policies_and_guidance.models import (
    PoliciesAndGuidance,
)

from tools.models import ToolsHome

from news.models import (
    NewsHome,
)

from wagtailmenus.models import MainMenu, MainMenuItem, Site

from home.models import HomePage

from news.models import (
    NewsHome,
)


class Command(BaseCommand):
    help = "Create menus"

    def handle(self, *args, **options):
        site = Site.objects.first()

        main_menu = MainMenu.objects.filter(
            site=site,
        ).first()

        if not main_menu:
            main_menu = MainMenu.objects.create(
                site=site,
            )

        home_page = HomePage.objects.all()
        news_home = NewsHome.objects.all()

        main_menu.add_menu_items_for_pages(home_page)
        main_menu.add_menu_items_for_pages(news_home)
