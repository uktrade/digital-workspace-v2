from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


@pytest.mark.django_db
class ReportPageProblemTest(TestCase):
    def setUp(self):
        self.test_user_email = "test@test.com"
        self.test_password = "test_password"

        self.test_user, _ = get_user_model().objects.get_or_create(
            username="test_user",
            email=self.test_user_email,
        )
        self.test_user.set_password(self.test_password)
        self.test_user.save()
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
