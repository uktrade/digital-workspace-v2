from django.contrib.auth.management import create_permissions
from django.db import migrations
from wagtail.core.models import (
    Page,
    GroupPagePermission,
    GroupCollectionPermission,
    Collection,
)
from django.contrib.auth.models import User, Group, Permission

from django.core.management.base import BaseCommand

from news.models import NewsHome

from about_us.models import AboutUsHome
from networks.models import NetworksHome
from tools.models import ToolsHome
from transition.models import TransitionHome
from working_at_dit.models import (
    WorkingAtDITHome,
    TopicHome,
    PoliciesAndGuidanceHome,
    HowDoIHome,
)

top_level_page_types = [
    AboutUsHome,
    NetworksHome,
    ToolsHome,
    TransitionHome,
    WorkingAtDITHome,
    TopicHome,
    PoliciesAndGuidanceHome,
    HowDoIHome,
]

EDITOR_PAGE_PERMISSION_TYPES = [
    'add',
    'edit',
    'publish',
]

MODERATOR_PAGE_PERMISSION_TYPES = EDITOR_PAGE_PERMISSION_TYPES + [
    'lock',
    'unlock',
]


class Command(BaseCommand):
    help = "Create page permissions"

    def handle(self, *args, **options):
        # Remove standard groups
        editors, _ = Group.objects.get_or_create(
            name='Editors',
        )

        moderators, _ = Group.objects.get_or_create(
            name='Moderators',
        )

        moderators.delete()
        editors.delete()

        # Set up new groups
        viewers, _ = Group.objects.get_or_create(
            name='Viewers',
        )

        news_editors, _ = Group.objects.get_or_create(
            name='News editors',
        )

        news_moderators, _ = Group.objects.get_or_create(
            name='News Moderators',
        )

        editors, _ = Group.objects.get_or_create(
            name='Editors',
        )

        moderators, _ = Group.objects.get_or_create(
            name='Moderators',
        )

        moderators.permissions.clear()
        moderators.save()

        # Add wagtail admin permission
        wagtail_admin_permisson = Permission.objects.get(
            codename='access_admin'
        )

        news_editors.permissions.add(wagtail_admin_permisson)
        news_editors.save()

        news_moderators.permissions.add(wagtail_admin_permisson)
        news_moderators.save()

        news_permissions = [
            "add_newscategory",
            "change_newscategory",
            "view_newscategory",
        ]

        for news_permission in news_permissions:
            permisson = Permission.objects.get(
                codename=news_permission
            )

            news_editors.permissions.add(permisson)
            news_editors.save()

            news_moderators.permissions.add(permisson)
            news_moderators.save()

        editors.permissions.add(wagtail_admin_permisson)
        editors.save()

        moderators.permissions.add(wagtail_admin_permisson)
        moderators.save()

        # News
        news_home = NewsHome.objects.first()

        for identifier in EDITOR_PAGE_PERMISSION_TYPES:
            GroupPagePermission.objects.get_or_create(
                group=news_editors,
                page=news_home,
                permission_type=identifier,
            )

        for identifier in MODERATOR_PAGE_PERMISSION_TYPES:
            GroupPagePermission.objects.get_or_create(
                group=news_moderators,
                page=news_home,
                permission_type=identifier,
            )

        for top_level_page_type in top_level_page_types:
            top_level_page = top_level_page_type.objects.first()

            for identifier in EDITOR_PAGE_PERMISSION_TYPES:
                GroupPagePermission.objects.get_or_create(
                    group=editors,
                    page=top_level_page,
                    permission_type=identifier,
                )

            for identifier in MODERATOR_PAGE_PERMISSION_TYPES:
                GroupPagePermission.objects.get_or_create(
                    group=moderators,
                    page=top_level_page,
                    permission_type=identifier,
                )
