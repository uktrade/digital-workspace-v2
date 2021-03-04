from django.test import Client, TestCase

from user.test.factories import UserFactory


class TestSearchView(TestCase):
    def test_empty_query(self):
        user = UserFactory()
        c = Client()

        c.force_login(user)
        response = c.get("/search/", {"query": ""})

        self.assertEqual(response.status_code, 200)
