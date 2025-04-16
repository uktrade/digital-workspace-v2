import mohawk
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

url_name = "person-api-people-list"
test_url = f"http://testserver{reverse(url_name)}"


def hawk_auth_sender(
    key_id="some-id",
    secret_key="some-secret",
    url=test_url,
    method="GET",
    content="",
    content_type="",
):
    credentials = {
        "id": key_id,
        "key": secret_key,
        "algorithm": "sha256",
    }
    return mohawk.Sender(
        credentials,
        url,
        method,
        content=content,
        content_type=content_type,
    )


class HawkTests(TestCase):
    test_url = reverse("person-api-people-list")

    @override_settings(
        DJANGO_HAWK={
            "HAWK_INCOMING_ACCESS_KEY": "some-id",
            "HAWK_INCOMING_SECRET_KEY": "some-secret",
        }
    )
    def test_empty_object_returned_with_authentication(self):
        """If the Authorization and X-Forwarded-For headers are correct, then
        the correct, and authentic, data is returned
        """
        sender = hawk_auth_sender()
        response = APIClient().get(
            test_url,
            content_type="",
            HTTP_AUTHORIZATION=sender.request_header,
            HTTP_X_FORWARDED_FOR="1.2.3.4, 123.123.123.123",
        )
        assert response.status_code == status.HTTP_200_OK

    @override_settings(
        DJANGO_HAWK={
            "HAWK_INCOMING_ACCESS_KEY": "wrong-id",
            "HAWK_INCOMING_SECRET_KEY": "some-secret",
        }
    )
    def test_bad_credentials_mean_401_returned(self):
        """If the wrong credentials are used,
        then a 401 is returned
        """
        sender = hawk_auth_sender()
        response = APIClient().get(
            test_url,
            content_type="",
            HTTP_AUTHORIZATION=sender.request_header,
            HTTP_X_FORWARDED_FOR="1.2.3.4, 123.123.123.123",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        error = {"detail": "Incorrect authentication credentials."}
        assert response.json() == error


class PersonTests(TestCase):
    test_url = reverse("person-api-people-list")

    @override_settings(
        DJANGO_HAWK={
            "HAWK_INCOMING_ACCESS_KEY": "some-id",
            "HAWK_INCOMING_SECRET_KEY": "some-secret",
        }
    )
    def test_person_returned_with_authentication(self):
        """If the Authorization and X-Forwarded-For headers are correct, then
        the correct, and authentic, data is returned
        """
        sender = hawk_auth_sender()
        response = APIClient().get(
            test_url,
            content_type="",
            HTTP_AUTHORIZATION=sender.request_header,
            HTTP_X_FORWARDED_FOR="1.2.3.4, 123.123.123.123",
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["results"]) == 1
        person_returned = response.json()["results"][0]

        assert person_returned["full_name"] == "J Smith"
        assert person_returned["formatted_roles"] == ["Software Engineer in Software"]
        roles = person_returned["roles"]
        assert isinstance(roles, list)
        assert len(roles) == 1
        assert roles[0]["role"] == "Software Engineer"

        # sso_user_id = user.username = new format staff sso id
        assert person_returned["sso_user_id"] == "johnsmith"
