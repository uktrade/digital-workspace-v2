from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from peoplefinder.services.person import PersonService
from peoplefinder.test.factories import UserWithPersonFactory


@pytest.mark.django_db
class ReportPageProblemTest(TestCase):
    def setUp(self):
        self.test_user = UserWithPersonFactory()
        self.client.force_login(self.test_user)

    @mock.patch("core.views.NotificationsAPIClient.send_email_notification")
    def test_page_problem_found_view(
        self,
        send_email_notification,
    ):
        url = reverse("page_problem_found")

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            url,
            {
                "page_url": "http://any-url-will-do.com/somewhere/here?answer=42",
                "trying_to": "test",
                "what_went_wrong": "test",
            },
        )

        self.assertEqual(response.status_code, 200)
        send_email_notification.assert_called_once()
