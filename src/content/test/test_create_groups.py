from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase

from content.management.commands.create_groups import TOP_LEVEL_PAGE_TYPES
from news.models import NewsHome


class CreateGroupsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("create_section_homepages")
        call_command("create_groups")

        cls.editors = Group.objects.get(name="Editors")
        cls.moderators = Group.objects.get(name="Moderators")
        cls.news_moderators = Group.objects.get(name="News Moderators")

    def test_new_groups_have_admin(self):
        self.news_moderators.permissions.get(codename="access_admin")

    def test_permissions(self):
        # news moderators have the same collection permissions as moderators
        # apart from the document choose permission
        moderator_permissions = self.news_moderators.collection_permissions.all()
        moderator_permission_codenames = [
            x.permission.codename for x in moderator_permissions
        ]
        self.assertEqual(
            moderator_permission_codenames,
            ['add_document', 'change_document', 'choose_document', 'add_image', 'change_image', 'choose_image', 'add_media', 'change_media'],
        )

        news_moderator_permissions = self.news_moderators.collection_permissions.all()
        news_moderator_permission_codenames = [
            x.permission.codename for x in news_moderator_permissions
        ]
        self.assertEqual(
            news_moderator_permission_codenames,
            ['add_document', 'change_document', 'choose_document', 'add_image', 'change_image', 'choose_image', 'add_media', 'change_media'],
        )

        # news moderators have newscategory permissions
        self.assertEqual(
            self.news_moderators.permissions.filter(
                codename__endswith="newscategory"
            ).count(),
            4,
        )

    def test_page_permissions(self):
        news_home = NewsHome.objects.first()

        # they have page permissions for the news home page
        self.assertTrue(
            self.news_moderators.page_permissions.filter(page=news_home).count()
        )

        # editors/moderators have page permissions for other pages

        # `specific_deferred` returns the most specific subclassed form of the
        # page which matches what we get back for `top_level_pages`
        # https://docs.wagtail.io/en/stable/reference/pages/model_reference.html#wagtail.models.Page.get_specific
        editors_pages = [
            x.page.specific_deferred for x in self.editors.page_permissions.all()
        ]
        moderators_pages = [
            x.page.specific_deferred for x in self.moderators.page_permissions.all()
        ]
        top_level_pages = [x.objects.first() for x in TOP_LEVEL_PAGE_TYPES]

        self.assertEqual(set(editors_pages), set(top_level_pages))
        self.assertEqual(set(moderators_pages), set(top_level_pages))
