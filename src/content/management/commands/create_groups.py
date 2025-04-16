from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from wagtail.models import Collection, GroupCollectionPermission, GroupPagePermission

from about_us.models import AboutUsHome
from events.models import EventsHome
from home.models import HomePage
from networks.models import NetworksHome
from news.models import NewsHome
from tools.models import ToolsHome
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
    WorkingAtDITHome,
    EventsHome,
]


EDITOR_PAGE_PERMISSIONS = [
    "add_page",
    "change_page",
    "publish_page",
]

MODERATOR_PAGE_PERMISSIONS = EDITOR_PAGE_PERMISSIONS + [
    "lock_page",
    "unlock_page",
]

MODERATOR_ROOT_COLLECTION_PERMISSIONS = [
    "add_media",
    "change_media",
    "add_image",
    "change_image",
    "choose_image",
    "add_document",
    "change_document",
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

SITE_ALERT_BANNER_ADMIN_GROUP_NAME = "Site Alert Banner Admin"
SITE_ALERT_BANNER_ADMIN_PERMISSIONS = [
    "add_sitealertbanner",
    "change_sitealertbanner",
    "delete_sitealertbanner",
    "view_sitealertbanner",
]

EVENT_CREATORS_GROUP_NAME = "Event Creators"
EVENT_CREATORS_ROOT_COLLECTION_PERMISSIONS = [
    "add_media",
    "change_media",
    "add_image",
    "change_image",
    "choose_image",
    "add_document",
    "change_document",
    "choose_document",
]
EVENT_CREATORS_PAGE_PERMISSIONS = [
    "add_page",
    "publish_page",
]

EVENT_EDITORS_GROUP_NAME = "Event Editors"
EVENT_EDITORS_ROOT_COLLECTION_PERMISSIONS = [
    "add_media",
    "change_media",
    "add_image",
    "change_image",
    "choose_image",
    "add_document",
    "change_document",
    "choose_document",
]
EVENT_EDITORS_PAGE_PERMISSIONS = EVENT_CREATORS_PAGE_PERMISSIONS + [
    "change_page",
    "lock_page",
    "unlock_page",
]

HOME_EDITORS_GROUP_NAME = "Home page editors"
HOME_EDITORS_ROOT_COLLECTION_PERMISSIONS = [
    "add_media",
    "change_media",
    "add_image",
    "change_image",
    "choose_image",
]
HOME_EDITORS_USER_PERMISSIONS = [
    "can_change_home_page_content",
]

SEARCH_EXPORTERS_GROUP_NAME = "Search Exporters"
SEARCH_EXPORTERS_PERMISSIONS = [
    "export_search",
]


class Command(BaseCommand):
    help = "Create page permissions"

    def grant_wagtail_admin_perm(self, group):
        wagtail_admin_permission = Permission.objects.get(codename="access_admin")
        group.permissions.add(wagtail_admin_permission)

    def grant_group_collection_perms(self, group, permissions):
        root_collection_permissions = Permission.objects.filter(
            codename__in=permissions
        )
        for permission in root_collection_permissions:
            GroupCollectionPermission.objects.get_or_create(
                group=group,
                collection=self.root_collection,
                permission=permission,
            )

    def grant_page_perms(self, group, page_type, permissions):
        page = page_type.objects.first()
        for page_perm in permissions:
            GroupPagePermission.objects.get_or_create(
                group=group,
                page=page,
                permission=Permission.objects.get(
                    codename=page_perm,
                    content_type__app_label="wagtailcore",
                ),
            )

    def home_page_permissions(self):
        home_editors_group, _ = Group.objects.get_or_create(
            name=HOME_EDITORS_GROUP_NAME
        )
        self.grant_wagtail_admin_perm(home_editors_group)

        # Home page editors permissions
        self.grant_group_collection_perms(
            home_editors_group,
            HOME_EDITORS_ROOT_COLLECTION_PERMISSIONS,
        )

        # Home page editors get the user permission to change the homepage content
        home_page = HomePage.objects.first()
        GroupPagePermission.objects.get_or_create(
            group=home_editors_group,
            page=home_page,
            permission=Permission.objects.get(
                codename="can_change_home_page_content",
                content_type__app_label="home",
            ),
        )

    def event_permissions(self):
        event_creators_group, _ = Group.objects.get_or_create(
            name=EVENT_CREATORS_GROUP_NAME
        )
        event_editors_group, _ = Group.objects.get_or_create(
            name=EVENT_EDITORS_GROUP_NAME
        )
        self.grant_wagtail_admin_perm(event_creators_group)
        self.grant_wagtail_admin_perm(event_editors_group)

        # Event creators root collection permissions
        self.grant_group_collection_perms(
            event_creators_group,
            EVENT_CREATORS_ROOT_COLLECTION_PERMISSIONS,
        )
        # Event editors root collection permissions
        self.grant_group_collection_perms(
            event_editors_group,
            EVENT_EDITORS_ROOT_COLLECTION_PERMISSIONS,
        )

        # Event creators can add child pages below the EventsHome page
        self.grant_page_perms(
            event_creators_group,
            EventsHome,
            EVENT_CREATORS_PAGE_PERMISSIONS,
        )
        # Event editors can add/edit/delete/view EventsHome page and all of
        # its children
        self.grant_page_perms(
            event_editors_group,
            EventsHome,
            EVENT_EDITORS_PAGE_PERMISSIONS,
        )

    def search_exporters_permissions(self):
        search_exporters_group, _ = Group.objects.get_or_create(
            name=SEARCH_EXPORTERS_GROUP_NAME
        )

        search_exporters_group.permissions.set(
            Permission.objects.filter(
                codename__in=SEARCH_EXPORTERS_PERMISSIONS,
                content_type__app_label="extended_search",
            )
        )

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

        # Root collection permissions
        self.root_collection = Collection.objects.get(name="Root")

        # Moderator root collection permissions
        root_collection_moderator_permissions = Permission.objects.filter(
            codename__in=MODERATOR_ROOT_COLLECTION_PERMISSIONS
        )
        for permission in root_collection_moderator_permissions:
            GroupCollectionPermission.objects.get_or_create(
                group=moderators,
                collection=self.root_collection,
                permission=permission,
            )

        # News moderator root collection permissions
        root_collection_new_moderator_permissions = Permission.objects.filter(
            codename__in=NEWS_MODERATOR_ROOT_COLLECTION_PERMISSIONS
        )
        for permission in root_collection_new_moderator_permissions:
            GroupCollectionPermission.objects.get_or_create(
                group=news_moderators,
                collection=self.root_collection,
                permission=permission,
            )

        # News
        news_home = NewsHome.objects.first()

        for moderator_page_permission in MODERATOR_PAGE_PERMISSIONS:
            GroupPagePermission.objects.get_or_create(
                group=news_moderators,
                page=news_home,
                permission=Permission.objects.get(
                    codename=moderator_page_permission,
                    content_type__app_label="wagtailcore",
                ),
            )

        GroupPagePermission.objects.filter(
            group=editors,
        ).delete()

        GroupPagePermission.objects.filter(
            group=moderators,
        ).delete()

        for top_level_page_type in TOP_LEVEL_PAGE_TYPES:
            top_level_page = top_level_page_type.objects.first()

            for editor_page_permission in EDITOR_PAGE_PERMISSIONS:
                GroupPagePermission.objects.get_or_create(
                    group=editors,
                    page=top_level_page,
                    permission=Permission.objects.get(
                        codename=editor_page_permission,
                        content_type__app_label="wagtailcore",
                    ),
                )

            for moderator_page_permission in MODERATOR_PAGE_PERMISSIONS:
                GroupPagePermission.objects.get_or_create(
                    group=moderators,
                    page=top_level_page,
                    permission=Permission.objects.get(
                        codename=moderator_page_permission,
                        content_type__app_label="wagtailcore",
                    ),
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

        site_alert_banner_admin_group, _ = Group.objects.get_or_create(
            name=SITE_ALERT_BANNER_ADMIN_GROUP_NAME
        )
        site_alert_banner_admin_group.permissions.set(
            Permission.objects.filter(
                codename__in=SITE_ALERT_BANNER_ADMIN_PERMISSIONS,
                content_type__app_label="core",
            )
        )

        self.home_page_permissions()
        self.event_permissions()
        self.search_exporters_permissions()
