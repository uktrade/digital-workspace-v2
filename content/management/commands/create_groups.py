from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from wagtail.core.models import (
    GroupPagePermission,
)

from about_us.models import AboutUsHome
from networks.models import NetworksHome
from news.models import NewsHome
from tools.models import ToolsHome
from transition.models import TransitionHome
from working_at_dit.models import (
    HowDoIHome,
    PoliciesAndGuidanceHome,
    TopicHome,
    WorkingAtDITHome,
)

top_level_page_types = [
    AboutUsHome,
    HowDoIHome,
    NetworksHome,
    PoliciesAndGuidanceHome,
    ToolsHome,
    TopicHome,
    TransitionHome,
    WorkingAtDITHome,
]

EDITOR_PAGE_PERMISSION_TYPES = [
    "add",
    "edit",
    "publish",
]

MODERATOR_PAGE_PERMISSION_TYPES = EDITOR_PAGE_PERMISSION_TYPES + [
    "lock",
    "unlock",
]


class Command(BaseCommand):
    help = "Create page permissions"

    def handle(self, *args, **options):
        # Set up new groups
        # viewers, _ = Group.objects.get_or_create(
        #     name='Viewers',
        # )

        news_editors, _ = Group.objects.get_or_create(
            name="News editors",
        )

        news_moderators, _ = Group.objects.get_or_create(
            name="News Moderators",
        )

        editors = Group.objects.filter(
            name="Editors",
        ).first()

        moderators = Group.objects.filter(
            name="Moderators",
        ).first()

        # Add wagtail admin permission
        wagtail_admin_permission = Permission.objects.get(codename="access_admin")

        # viewers.permissions.add(wagtail_admin_permission)

        news_editors.permissions.add(wagtail_admin_permission)
        news_editors.save()

        news_moderators.permissions.add(wagtail_admin_permission)
        news_moderators.save()

        news_permissions = [
            "add_newscategory",
            "change_newscategory",
            "view_newscategory",
            "add_image",
            "change_image",
            "delete_image",
            "view_image",
            "add_document",
            "change_document",
            "delete_document",
            "view_document",
            "add_media",
            "change_media",
            "delete_media",
            "view_media",
        ]

        for news_permission in news_permissions:
            permission = Permission.objects.get(codename=news_permission)

            news_editors.permissions.add(permission)
            news_editors.save()

            news_moderators.permissions.add(permission)
            news_moderators.save()

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

        GroupPagePermission.objects.filter(
            group=editors,
        ).delete()

        GroupPagePermission.objects.filter(
            group=moderators,
        ).delete()

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

        moderator_permissions = [
            "add_quicklink",
            "change_quicklink",
            "delete_quicklink",
            "view_quicklink",
            "view_whatspopular",
            "add_whatspopular",
            "change_whatspopular",
            "delete_whatspopular",
            "delete_sitealertbanner",
            "view_sitealertbanner",
            "add_sitealertbanner",
            "change_sitealertbanner",
            "add_howdoipreview",
            "view_howdoipreview",
            "delete_howdoipreview",
            "change_howdoipreview",
            "add_comment",
            "change_comment",
            "delete_comment",
            "view_comment",
        ]

        for moderator_permission in moderator_permissions:
            permissions = Permission.objects.filter(codename=moderator_permission)

            for permission in permissions:
                moderators.permissions.add(permission)
                moderators.save()

        # Make it so all groups can view all pages
        # home = HomePage.objects.first()
        #
        # for group in [
        #     viewers,
        # ]:
        #     GroupPagePermission.objects.get_or_create(
        #         group=group,
        #         page=home,
        #         permission_type="edit",
        #     )
