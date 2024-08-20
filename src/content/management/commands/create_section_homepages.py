from datetime import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone
from wagtail.models import Page

from about_us.models import AboutUsHome
from content.models import BlogIndex, ContentPage
from country_fact_sheet.models import CountryFactSheetHome
from events.models import EventsHome
from networks.models import NetworksHome
from news.models import NewsHome
from tools.models import ToolsHome
from working_at_dit.models import (
    GuidanceHome,
    HowDoIHome,
    PoliciesAndGuidanceHome,
    PoliciesHome,
    TopicHome,
    WorkingAtDITHome,
)


class Command(BaseCommand):
    help = "Create section homepages"

    def handle(self, *args, **options):
        home_page = Page.objects.filter(slug="home").first()

        #  Cookies
        try:
            Page.objects.get(slug="cookies")
        except Page.DoesNotExist:
            cookie_explanation = ContentPage(
                title="Cookies",
                slug="cookies",
                live=True,
                first_published_at=datetime.now(),
                show_in_menus=False,
                depth=8,
            )

            home_page.add_child(instance=cookie_explanation)
            home_page.save()

            cookie_explanation.save_revision().publish()

        try:
            Page.objects.get(slug="news-and-views")
        except Page.DoesNotExist:
            news_home = NewsHome(
                title="News",
                slug="news-and-views",
                live=True,
                first_published_at=datetime.now(),
                show_in_menus=True,
                depth=1,
                legacy_path="/news-and-views/",
            )

            home_page.add_child(instance=news_home)
            home_page.save()

            news_home.save_revision().publish()

        try:
            Page.objects.get(slug="events")
        except Page.DoesNotExist:
            events_home = EventsHome(
                title="Events",
                slug="events",
                live=True,
                first_published_at=datetime.now(),
                show_in_menus=True,
                depth=1,
                legacy_path="/events/",
            )

            home_page.add_child(instance=events_home)
            home_page.save()

            events_home.save_revision().publish()

        try:
            Page.objects.get(slug="working-at-dbt")
        except Page.DoesNotExist:
            working_at_dit_home = WorkingAtDITHome(
                title="Working at DBT",
                slug="working-at-dbt",
                live=True,
                first_published_at=datetime.now(),
                show_in_menus=True,
                depth=3,
                legacy_path="/working-at-dit/",
            )

            home_page.add_child(instance=working_at_dit_home)
            home_page.save()

            working_at_dit_home.save_revision().publish()

        try:
            Page.objects.get(slug="topics")
        except Page.DoesNotExist:
            topic_home = TopicHome(
                title="Topics",
                slug="topics",
                live=True,
                first_published_at=datetime.now(),
                show_in_menus=True,
                depth=1,
                legacy_path="/topics/",
            )

            working_at_dit_home.add_child(instance=topic_home)
            working_at_dit_home.save()

            topic_home.save_revision().publish()

        try:
            Page.objects.get(slug="how-do-i")
        except Page.DoesNotExist:
            how_do_i = HowDoIHome(
                title="All How Do I? guides",
                slug="how-do-i",
                live=True,
                first_published_at=datetime.now(),
                show_in_menus=True,
                depth=2,
                legacy_path="/working-at-dit/how-do-i/",
            )

            working_at_dit_home.add_child(instance=how_do_i)
            working_at_dit_home.save()

            how_do_i.save_revision().publish()

        try:
            Page.objects.get(slug="policies-and-guidance")
        except Page.DoesNotExist:
            policies_and_guidance = PoliciesAndGuidanceHome(
                title="Policies and Guidance",
                slug="policies-and-guidance",
                live=True,
                first_published_at=datetime.now(),
                show_in_menus=True,
                depth=3,
                legacy_path="/working-at-dit/policies-and-guidance/",
            )

            working_at_dit_home.add_child(instance=policies_and_guidance)
            working_at_dit_home.save()

            policies_and_guidance.save_revision().publish()

        try:
            Page.objects.get(slug="policies")
        except Page.DoesNotExist:
            policies = PoliciesHome(
                title="Policies",
                slug="policies",
                live=True,
                first_published_at=datetime.now(),
                show_in_menus=True,
                depth=1,
            )

            policies_and_guidance.add_child(instance=policies)
            policies_and_guidance.save()

            policies.save_revision().publish()

        try:
            Page.objects.get(slug="guidance")
        except Page.DoesNotExist:
            guidance = GuidanceHome(
                title="Guidance",
                slug="guidance",
                live=True,
                first_published_at=datetime.now(),
                show_in_menus=True,
                depth=2,
            )

            policies_and_guidance.add_child(instance=guidance)
            policies_and_guidance.save()

            guidance.save_revision().publish()

            #  About Us
        try:
            Page.objects.get(slug="about-us")
        except Page.DoesNotExist:
            about_us = AboutUsHome(
                title="About Us",
                slug="about-us",
                live=True,
                first_published_at=datetime.now(),
                show_in_menus=True,
                depth=4,
                legacy_path="/about-us/",
            )

            home_page.add_child(instance=about_us)
            home_page.save()

            about_us.save_revision().publish()

        try:
            Page.objects.get(slug="tools")
        except Page.DoesNotExist:
            tools_home = ToolsHome(
                title="Tools",
                slug="tools",
                live=True,
                first_published_at=datetime.now(),
                show_in_menus=True,
                depth=5,
                legacy_path="/tools/",
            )

            home_page.add_child(instance=tools_home)
            home_page.save()

            tools_home.save_revision().publish()

        try:
            Page.objects.get(slug="networks")
        except Page.DoesNotExist:
            networks = NetworksHome(
                title="Networks",
                slug="networks",
                live=True,
                first_published_at=datetime.now(),
                show_in_menus=True,
                depth=6,
                legacy_path="/networks/",
            )

            home_page.add_child(instance=networks)
            home_page.save()

            networks.save_revision().publish()

        try:
            Page.objects.get(slug="country-fact-sheets")
        except Page.DoesNotExist:
            country_fact_sheet_homepage = CountryFactSheetHome(
                title="Trade statistics country fact sheets",
                slug="country-fact-sheets",
                live=True,
                first_published_at=datetime.now(),
                show_in_menus=True,
                depth=2,
                legacy_path="/working-at-dit/policies-and-guidance/trade-statistics-country-factsheets/",
            )

            home_page.add_child(instance=country_fact_sheet_homepage)
            home_page.save()

            country_fact_sheet_homepage.save_revision().publish()

        # Blogs
        try:
            Page.objects.get(slug="blogs")
        except Page.DoesNotExist:
            self.stdout.write("Creating BlogIndex")
            blog_index = BlogIndex(
                title="Blogs",
                slug="blogs",
                live=True,
                first_published_at=timezone.now(),
                show_in_menus=True,
                legacy_path=None,
            )

            home_page.add_child(instance=blog_index)
            home_page.save()

            blog_index.save_revision().publish()
        else:
            self.stdout.write("BlogIndex already found")
