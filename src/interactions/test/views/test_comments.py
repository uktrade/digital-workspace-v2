import pytest
from django.test.client import Client
from django.urls import reverse
from core.models import FeatureFlag
from news.factories import CommentFactory
from news.models import Comment

pytestmark = pytest.mark.django_db


def test_hide_comment_view(mocker):
    comment = CommentFactory()
    client = Client()
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


def test_comment_on_page_view(news_page, user):
    client = Client()
    client.force_login(user)
    FeatureFlag.objects.create(name="new_comments", everyone=True)

    url = reverse("interactions:comment-on-page", args=[news_page.id])
    comment_content = "a new comment"

    response = client.post(
        path=url,
        data={
            "comment": comment_content,
        },
    )

    # Test view contains new comment within the response template
    assert response.status_code == 200
    assert comment_content in response.content.decode()


# @pytest.mark.skip(reason="TODO")
def test_edit_comment_view(mocker, user):
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
    mocker.patch("interactions.services.comments.can_edit_comment", return_value=True)
    response = client.post(**request)
    assert response.status_code == 200
    assert comment_content in response.content.decode()

    # Test view when the user IS NOT authorised to edit the comment
    mocker.patch("interactions.services.comments.can_edit_comment", return_value=False)
    response = client.post(**request)
    assert response.status_code == 403
    assert not response.content


def test_edit_comment_form_view(mocker, user):
    comment = CommentFactory()
    client = Client()
    client.force_login(user)

    url = reverse("interactions:edit-comment-form", args=[comment.id])

    # Test view when the user IS authorised to edit the comment
    mocker.patch("interactions.services.comments.can_edit_comment", return_value=True)
    response = client.get(url)
    assert response.status_code == 200
    assert f'id="comment-{ comment.id }-edit-form"' in response.content.decode()
    assert comment.content in response.content.decode()

    # Test view when the user IS NOT authorised to edit the comment
    mocker.patch("interactions.services.comments.can_edit_comment", return_value=False)
    response = client.get(url)
    assert response.status_code == 403
    assert not response.content


def test_get_comment_view(user):
    comment = CommentFactory()
    client = Client()
    client.force_login(user)

    url = lambda comment_id: reverse("interactions:get-comment", args=[comment_id])

    # Test view when a valid comment is passed
    response = client.get(url(comment.id))
    assert response.status_code == 200
    assert comment.content in response.content.decode()

    # Test view when an invalid comment is passed
    response = client.get(url(123456))
    assert response.status_code == 404


def test_get_page_comments_view(user, news_page):
    comments = CommentFactory.create_batch(3, page=news_page)
    client = Client()
    client.force_login(user)

    url = lambda page_id: reverse("interactions:get-page-comments", args=[page_id])

    # Test view when a valid page is passed
    response = client.get(url(news_page.id))
    assert response.status_code == 200
    for comment in comments:
        assert f"comment-{comment.id}" in response.content.decode()
        assert comment.content in response.content.decode()

    # Test view when an invalid page is passed
    response = client.get(url(123456))
    assert response.status_code == 404


def test_reply_to_comment_view(mocker, user):
    comment = CommentFactory()
    client = Client()
    client.force_login(user)

    url = reverse("interactions:reply-comment", args=[comment.id])
    comment_content = "a comment reply"

    request = {
        "path": url,
        "data": {
            "comment": comment_content,
        },
    }

    # Test view when the user IS authorised to reply to the comment
    mocker.patch("interactions.services.comments.can_reply_comment", return_value=True)
    response = client.post(**request)
    reply = Comment.objects.get(parent=comment)
    assert reply.content == comment_content
    assert response.status_code == 200
    assert comment_content in response.content.decode()

    # Test view when the user IS NOT authorised to reply to the comment
    mocker.patch("interactions.services.comments.can_reply_comment", return_value=False)
    response = client.post(**request)
    assert response.status_code == 403
    assert not response.content
