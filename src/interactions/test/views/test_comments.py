import pytest
from django.test.client import Client
from django.urls import reverse
from django.test import override_settings
from core.models import FeatureFlag

pytestmark = pytest.mark.django_db


def test_hide_comment_view(comment, mocker):
    client = Client()
    url = reverse("interactions:hide-comment", args=[comment.id])

    # Test view when the user IS authorised to delete comment
    mocker.patch("interactions.services.comments.can_hide_comment", return_value=True)
    response = client.post(url)
    assert response.status_code == 200

    # Test view when the user IS NOT authorised to delete comment
    mocker.patch("interactions.services.comments.can_hide_comment", return_value=False)
    response = client.post(url)
    assert response.status_code == 403


# @pytest.mark.skip(reason="TODO")
def test_comment_on_page_view(comment, mocker, test_user):
    client = Client()
    url = reverse("interactions:comment-on-page", args=[comment.page.id])
    client.force_login(test_user)
    FeatureFlag.objects.create(name="new_comments", everyone=True)
    response = client.post(
        url,
        data={
            "comment": "a new comment",
        },
    )

    print("TEST_RESPONSE")
    print(response)
    assert response.status_code == 200


@pytest.mark.skip(reason="TODO")
def test_edit_comment_view(comment, mocker):
    pass


@pytest.mark.skip(reason="TODO")
def test_edit_comment_form_view(comment, mocker):
    pass


@pytest.mark.skip(reason="TODO")
def test_get_comment_view(comment, mocker):
    pass


@pytest.mark.skip(reason="TODO")
def test_get_page_comments_view(comment, mocker):
    pass


@pytest.mark.skip(reason="TODO")
def test_reply_to_comment_view(comment, mocker):
    pass
