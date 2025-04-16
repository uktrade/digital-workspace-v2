from django.core.management.base import BaseCommand
from wagtailmenus.models import MainMenu, Site

from about_us.models import AboutUsHome
from news.models import NewsHome
from tools.models import ToolsHome
from working_at_dit.models import WorkingAtDITHome


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

        # if main_menu.get_base_page_queryset().count() < 5:
        news_home = NewsHome.objects.all()
        working_at_dit_home = WorkingAtDITHome.objects.all()
        about_us_home = AboutUsHome.objects.all()
        tools_home = ToolsHome.objects.all()

        main_menu.add_menu_items_for_pages(news_home)
        main_menu.add_menu_items_for_pages(working_at_dit_home)
        main_menu.add_menu_items_for_pages(about_us_home)
        main_menu.add_menu_items_for_pages(tools_home)
