from django.core.management.base import BaseCommand
from wagtailmenus.models import FlatMenu, FlatMenuItem, MainMenu, Site

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

            news_home = NewsHome.objects.all()
            working_at_dit_home = WorkingAtDITHome.objects.all()
            about_us_home = AboutUsHome.objects.all()
            tools_home = ToolsHome.objects.all()

            main_menu.add_menu_items_for_pages(news_home)
            main_menu.add_menu_items_for_pages(working_at_dit_home)
            main_menu.add_menu_items_for_pages(about_us_home)
            main_menu.add_menu_items_for_pages(tools_home)

        flat_main, main_created = FlatMenu.objects.get_or_create(site=site, handle="main", title="Main")
        if main_created:
            flat_main.add_menu_items_for_pages(news_home)
            flat_main.add_menu_items_for_pages(tools_home)

        flat_working_here, wh_created = FlatMenu.objects.get_or_create(site=site, handle="working_here", title="Working here")
        if wh_created:
            flat_working_here.add_menu_items_for_pages(about_us_home)

        flat_people, people_created = FlatMenu.objects.get_or_create(site=site, handle="people", title="People")
        if people_created:
            p = FlatMenuItem(
                    menu=flat_people,
                    link_url="/discover/",
                    link_text="People",
                    sort_order=1,
                    allow_subnav=False,
                )
            flat_people.get_menu_items_manager().add(p)
            t = FlatMenuItem(
                    menu=flat_people,
                    link_url="/teams/",
                    link_text="Teams",
                    sort_order=2,
                    allow_subnav=False,
                )
            flat_people.get_menu_items_manager().add(t)
            flat_people.save()
