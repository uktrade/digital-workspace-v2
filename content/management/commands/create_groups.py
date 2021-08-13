from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from wagtail.core.models import (
    Collection,
    GroupCollectionPermission,
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

TOP_LEVEL_PAGE_TYPES = [
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

NEWS_MODERATOR_ROOT_COLLECTION_PERMISSIONS = [
    "add_media",
    "change_media",
    "add_image",
    "change_image",
    "choose_image",
    "add_document",
    "change_document",
    "choose_document",
]

MODERATOR_PERMISSIONS = [
    # quicklink
    "add_quicklink",
    "change_quicklink",
    "delete_quicklink",
    "view_quicklink",
    # whatspopular
    "add_whatspopular",
    "change_whatspopular",
    "delete_whatspopular",
    "view_whatspopular",
    # sitealertbanner
    "add_sitealertbanner",
    "change_sitealertbanner",
    "delete_sitealertbanner",
    "view_sitealertbanner",
    # hodoipreview
    "add_howdoipreview",
    "change_howdoipreview",
    "delete_howdoipreview",
    "view_howdoipreview",
    # comment
    "add_comment",
    "change_comment",
    "delete_comment",
    "view_comment",
    # Add missing choose document permission
    "choose_document",
    # Users
    "change_user",
    # Document and document history
    "view_historicaldocument",
    "view_document",
]

NEWS_MODERATOR_PERMISSIONS = [
    # newscategory
    "add_newscategory",
    "change_newscategory",
    "delete_newscategory",
    "view_newscategory",
]


class Command(BaseCommand):
    help = "Create page permissions"

    def handle(self, *args, **options):
        news_moderators, _ = Group.objects.get_or_create(
            name="News Moderators",
        )

        editors = Group.objects.get(name="Editors")

        moderators = Group.objects.get(name="Moderators")

        wagtail_admin_permission = Permission.objects.get(codename="access_admin")

        # Add the wagtail admin permission and moderators permissions
        # to the news moderators groups
        news_moderators.permissions.add(wagtail_admin_permission)
        news_moderators.save()

        root_collection = Collection.objects.get(name="Root")
        root_collection_permissions = Permission.objects.filter(
            codename__in=NEWS_MODERATOR_ROOT_COLLECTION_PERMISSIONS
        )

        for permission in root_collection_permissions:
            GroupCollectionPermission.objects.get_or_create(
                group=news_moderators,
                collection=root_collection,
                permission=permission,
            )

        # News
        news_home = NewsHome.objects.first()

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

        for top_level_page_type in TOP_LEVEL_PAGE_TYPES:
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

        moderator_permissions = Permission.objects.filter(
            codename__in=MODERATOR_PERMISSIONS
        )
        moderators.permissions.add(*moderator_permissions)
        moderators.save()

        news_moderator_permissions = Permission.objects.filter(
            codename__in=NEWS_MODERATOR_PERMISSIONS
        )
        news_moderators.permissions.add(*news_moderator_permissions)
        news_moderators.save()
