from unittest import mock
import pytest
from django.test.client import Client
from django.urls import reverse
from news.factories import CommentFactory
from news.models import Comment
from waffle.testutils import override_flag

pytestmark = pytest.mark.django_db


def test_hide_comment_view(mocker, user):
    comment = CommentFactory()
    client = Client()
    client.force_login(user)
    url = reverse("interactions:hide-comment", args=[comment.id])

    # Test view when the user IS authorised to delete comment
    mocker.patch("interactions.services.comments.can_hide_comment", return_value=True)
    response = client.post(url)
    assert response.status_code == 200
    assert comment.content not in response.content.decode()

    # Test view when the user IS NOT authorised to delete comment
    mocker.patch("interactions.services.comments.can_hide_comment", return_value=False)
    response = client.post(url)
    assert response.status_code == 403
    assert not response.content


def test_comment_on_page_view(mocker, news_page, user):
    client = Client()
    client.force_login(user)

    comment_content = "a new comment"
    data = {
        "comment": comment_content,
    }

    url = reverse("interactions:comment-on-page", args=[news_page.pk])
    # Test view contains new comment within the response template
    response = client.post(path=url, data=data)
    assert response.status_code == 200
    assert comment_content in response.content.decode()

    # Test 404 is returned for an invalid page id
    url = reverse("interactions:comment-on-page", args=[123456])
    response = client.post(path=url, data=data)
    assert response.status_code == 404


@mock.patch("interactions.services.comments.can_edit_comment", return_value=True)
def test_edit_comment_view(mock_can_edit_comment, user):
    comment = CommentFactory()
    client = Client()
    client.force_login(user)

    url = reverse("interactions:edit-comment", args=[comment.id])
    comment_content = "an edited comment"

    request = {
        "path": url,
        "data": {
            "comment": comment_content,
        },
    }

    # Test view when the user IS authorised to edit the comment
    response = client.post(**request)
    assert response.status_code == 200
    assert comment_content in response.content.decode()

    # Test view when the user IS NOT authorised to edit the comment
    mock_can_edit_comment.return_value = False
    response = client.post(**request)
    assert response.status_code == 403
    assert not response.content


@mock.patch("interactions.services.comments.can_edit_comment", return_value=True)
def test_edit_comment_form_view(mock_can_edit_comment, user):
    comment = CommentFactory()
    client = Client()
    client.force_login(user)

    url = reverse("interactions:edit-comment-form", args=[comment.id])

    # Test view when the user IS authorised to edit the comment
    response = client.get(url)
    assert response.status_code == 200
    assert f'id="comment-{ comment.id }-edit-form"' in response.content.decode()
    assert comment.content in response.content.decode()
    assert response.context["comment"]["id"] == comment.id

    # Test view when an invalid comment ID is passed
    response = client.get(reverse("interactions:edit-comment-form", args=[123456]))
    assert response.status_code == 404

    # Test view when the user IS NOT authorised to edit the comment
    mock_can_edit_comment.return_value = False
    response = client.get(url)
    assert response.status_code == 403
    assert not response.content


def test_get_comment_view(user):
    comment = CommentFactory()
    client = Client()
    client.force_login(user)

    # Test view when a valid comment is passed
    response = client.get(reverse("interactions:get-comment", args=[comment.id]))
    assert response.status_code == 200
    assert comment.content in response.content.decode()
    assert response.context["comment"]["id"] == comment.id

    # Test view when an invalid comment is passed
    response = client.get(reverse("interactions:get-comment", args=[123456]))
    assert response.status_code == 404


def test_get_page_comments_view(user, news_page):
    comments = CommentFactory.create_batch(3, page=news_page)
    client = Client()
    client.force_login(user)

    # Test view when a valid page is passed
    response = client.get(
        reverse("interactions:get-page-comments", args=[news_page.id])
    )
    assert response.status_code == 200
    for comment in comments:
        assert f"comment-{comment.id}" in response.content.decode()
        assert comment.content in response.content.decode()

    # Test view when an invalid page is passed
    response = client.get(reverse("interactions:get-page-comments", args=[123456]))
    assert response.status_code == 404


@mock.patch("interactions.services.comments.can_reply_comment", return_value=True)
def test_reply_to_comment_view(mock_can_reply_comment, user):
    comment = CommentFactory()
    client = Client()
    client.force_login(user)

    url = reverse("interactions:reply-comment", args=[comment.id])
    comment_content = "a comment reply"
    data = {"comment": comment_content}

    # Test view when the user IS authorised to reply to the comment
    response = client.post(path=url, data=data)
    reply = Comment.objects.get(parent=comment)
    assert reply.content == comment_content
    assert response.status_code == 200
    assert comment_content in response.content.decode()
    assert response.context["comment"]["id"] == comment.id

    # Test view when an invalid comment ID is passed
    response = client.post(
        path=reverse("interactions:reply-comment", args=[123456]), data=data
    )
    assert response.status_code == 404

    # Test view when the user IS NOT authorised to reply to the comment
    mock_can_reply_comment.return_value = False
    response = client.post(path=url, data=data)
    assert response.status_code == 403
    assert not response.content
