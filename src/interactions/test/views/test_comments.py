import pytest
from django.test.client import Client
from django.urls import reverse

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


# TODO: other views to test
# comment_on_page
# edit_comment
# edit_comment_form
# get_comment
