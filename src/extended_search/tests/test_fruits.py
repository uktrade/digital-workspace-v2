from django.core.management import call_command
from django.test import TestCase

from news.factories import NewsPageFactory
from peoplefinder.services.person import PersonService
from tools.tests.factories import ToolFactory
from user.models import User
from user.test.factories import UserFactory
from working_at_dit.models import PoliciesAndGuidanceHome
from working_at_dit.tests.factories import GuidanceFactory, HowDoIFactory, PolicyFactory


class TestFruits(TestCase):
    def setUp(self):
        """
        Create the following data for search testing:
        - 1 guidance page with "fruit" in the title
        - 1 policy page with "fruit" in the title
        - 1 howdoi page with "fruit" in the title
        - 1 tool page with "fruit" in the title
        - 1 news page with "fruit" in the title
        """
        policies_and_guidance_home = PoliciesAndGuidanceHome.objects.first()
        self.content_owner = User.objects.get(username="johnsmith")
        self.content_owner_pages = [
            GuidanceFactory.create(
                parent=policies_and_guidance_home,
                title="How to eat Fruit",
                content_owner=self.content_owner.profile,
                content_contact_email=self.content_owner.email,
            ),
            PolicyFactory.create(
                parent=policies_and_guidance_home,
                title="What fruit can I eat?",
                content_owner=self.content_owner.profile,
                content_contact_email=self.content_owner.email,
            ),
            HowDoIFactory.create(
                title="How do I find fruit?",
                content_owner=self.content_owner.profile,
                content_contact_email=self.content_owner.email,
            ),
        ]
        self.pages = [
            ToolFactory.create(
                title="Fruit finder",
            ),
            NewsPageFactory.create(
                title="Big fruit news",
            ),
        ]

        call_command("update_index")

        self.user = UserFactory()
        PersonService().create_user_profile(self.user)
        self.client.force_login(self.user)

    def test_workspace(self):
        response = self.client.get("/search/", {"query": ""}, follow=True)
        self.assertEqual(response.status_code, 200)
        for page in self.content_owner_pages:
            self.assertNotContains(response, page.title)
        for page in self.pages:
            self.assertNotContains(response, page.title)

        self.assertContains(response, "All&nbsp;(0)")
        self.assertContains(response, "People&nbsp;(0)")
        self.assertContains(response, "Teams&nbsp;(0)")
        self.assertContains(response, "Guidance&nbsp;(0)")
        self.assertContains(response, "Tools&nbsp;(0)")
        self.assertContains(response, "News&nbsp;(0)")

    def test_fruits(self):
        response = self.client.get("/search/", {"query": "fruit"}, follow=True)
        self.assertEqual(response.status_code, 200)
        print(response.content)
        for page in self.content_owner_pages:
            self.assertContains(response, page.title)
        for page in self.pages:
            self.assertContains(response, page.title)

        self.assertContains(response, "All&nbsp;(5)")
        self.assertContains(response, "People&nbsp;(0)")
        self.assertContains(response, "Teams&nbsp;(0)")
        self.assertContains(response, "Guidance&nbsp;(2)")
        self.assertContains(response, "Tools&nbsp;(1)")
        self.assertContains(response, "News&nbsp;(1)")
