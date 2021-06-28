from django.shortcuts import reverse
from django.test import TestCase


class PingdomTest(TestCase):
    def test_ping_response(self):
        url = reverse("pingdom")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        assert "<status>OK</status>" in str(response.content)
        assert response.headers["content-type"] == "text/xml"
