from datetime import datetime

from django.core.management.base import BaseCommand

from wagtail.core.models import Page

from tools.models import ToolsHome

from news.models import (
    NewsHome,
)

from transition.models import TransitionHome

from about_us.models import AboutUsHome

from working_at_dit.models import (
    WorkingAtDITHome,
    HowDoIHome,
    TopicHome,
    PoliciesAndGuidanceHome,
    PoliciesHome,
    GuidanceHome,
)

from content.models import PrivacyPolicyHome

from networks.models import NetworksHome


def create_section_homepages():
    home_page = Page.objects.filter(slug="home").first()

    news_home = NewsHome(
        title="News",
        slug="news-and-views",
        live=True,
        first_published_at=datetime.now(),
        show_in_menus=True,
        depth=1,
    )

    home_page.add_child(instance=news_home)
    home_page.save()

    transition = TransitionHome(
        title="Transition",
        slug="transition",
        live=True,
        first_published_at=datetime.now(),
        show_in_menus=True,
        depth=2,
    )

    home_page.add_child(instance=transition)
    home_page.save()

    working_at_dit_home = WorkingAtDITHome(
        title="Working at DIT",
        slug="working-at-dit",
        live=True,
        first_published_at=datetime.now(),
        show_in_menus=True,
        depth=3,
    )

    home_page.add_child(instance=working_at_dit_home)
    home_page.save()

    topic_home = TopicHome(
        title="Topics",
        slug="topics",
        live=True,
        first_published_at=datetime.now(),
        show_in_menus=True,
        depth=1,
    )

    working_at_dit_home.add_child(instance=topic_home)
    working_at_dit_home.save()

    how_do_i = HowDoIHome(
        title="How Do I",
        slug="how-do-i",
        live=True,
        first_published_at=datetime.now(),
        show_in_menus=True,
        depth=2,
    )

    working_at_dit_home.add_child(instance=how_do_i)
    working_at_dit_home.save()

    policies_and_guidance = PoliciesAndGuidanceHome(
        title="Policies and Guidance",
        slug="policies-and-guidance",
        live=True,
        first_published_at=datetime.now(),
        show_in_menus=True,
        depth=3,
    )

    working_at_dit_home.add_child(instance=policies_and_guidance)
    working_at_dit_home.save()

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

    # About Us
    about_us = AboutUsHome(
        title="About Us",
        slug="about-us",
        live=True,
        first_published_at=datetime.now(),
        show_in_menus=True,
        depth=4,
    )

    home_page.add_child(instance=about_us)
    home_page.save()

    tools_home = ToolsHome(
        title="Tools",
        slug="tools",
        live=True,
        first_published_at=datetime.now(),
        show_in_menus=True,
        depth=5,
    )

    home_page.add_child(instance=tools_home)
    home_page.save()

    networks = NetworksHome(
        title="Networks",
        slug="networks",
        live=True,
        first_published_at=datetime.now(),
        show_in_menus=True,
        depth=6,
    )

    home_page.add_child(instance=networks)
    home_page.save()

    privacy_policy = PrivacyPolicyHome(
        title="Privacy Policy",
        slug="privacy-policy",
        live=True,
        first_published_at=datetime.now(),
        show_in_menus=True,
        depth=7,
    )

    home_page.add_child(instance=privacy_policy)
    home_page.save()
