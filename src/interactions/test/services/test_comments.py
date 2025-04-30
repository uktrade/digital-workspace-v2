import pytest
from interactions.services import comments as comments_service
from news.models import Comment
from news.factories import CommentFactory
from django.urls import reverse
from django.test import override_settings
from django.test import RequestFactory

from news.forms import CommentForm

pytestmark = pytest.mark.django_db


def test_show_comment():
    comment = CommentFactory.create(is_visible=False)
    comments_service.show_comment(comment)
    comment.refresh_from_db()
    assert comment.is_visible == True


def test_hide_comment():
    comment = CommentFactory.create()
    assert comment.is_visible == True
    comments_service.hide_comment(comment)
    comment.refresh_from_db()
    assert comment.is_visible == False


def test_can_hide_comment(user):
    comment = CommentFactory.create()

    # The user is the author of the comment
    assert comments_service.can_hide_comment(comment.author, comment) == True

    # The user is not the author of the comment
    assert comments_service.can_hide_comment(user, comment) == False

    # Test function called with comment_id instead of comment object
    assert comments_service.can_hide_comment(comment.author, comment.id) == True
    assert comments_service.can_hide_comment(user, comment.id) == False


def test_edit_comment():
    comment = CommentFactory.create()
    edited_content = "edited content of comment"
    comments_service.edit_comment(comment.id, edited_content)
    comment.refresh_from_db()
    assert comment.content == edited_content
    assert comment.edited_date is not None


def test_can_edit_comment(user):
    comment = CommentFactory.create()

    # The user is the author of the comment
    assert comments_service.can_edit_comment(comment.author, comment) == True

    # Test function called with comment_id instead of comment object
    assert comments_service.can_edit_comment(comment.author, comment.id) == True

    # The user is not the author of the comment
    assert comments_service.can_edit_comment(user, comment) == False

    # Test function called with comment_id instead of comment object
    assert comments_service.can_edit_comment(user, comment.id) == False


def test_add_page_comment(news_page, user):
    comment_content = "A new comment"
    comment = comments_service.add_page_comment(news_page, user, comment_content, None)

    # The comment is created succesfully
    assert isinstance(comment, Comment)
    assert comment.content == comment_content

    reply_content = "A comment reply"
    reply = comments_service.add_page_comment(
        news_page, user, reply_content, comment.pk
    )

    # The comment reply is created succesfully
    assert isinstance(reply, Comment)
    assert reply.content == reply_content
    assert reply.parent == comment


def test_get_page_comments(news_page):
    news_comments = CommentFactory.create_batch(3, page=news_page)
    hidden_news_comments = CommentFactory.create_batch(
        3, page=news_page, is_visible=False
    )
    comment = CommentFactory.create()
    news_page_comments = comments_service.get_page_comments(news_page)

    for news_comment in news_comments:
        # The comments are returned for the requested page
        assert news_comment in news_page_comments

    for hidden_news_comment in hidden_news_comments:
        # Hidden comments are not returned
        assert hidden_news_comment not in news_page_comments

    # Comments on other pages are not returned
    assert comment not in news_page_comments


def test_get_page_comment_count(news_page):
    comments = CommentFactory.create_batch(3, page=news_page)

    # Hidden comments are not included in the comment count
    CommentFactory.create_batch(5, page=news_page, is_visible=False)

    # The comment count is returned for the requested page
    assert comments_service.get_page_comment_count(news_page) == len(comments)


def test_get_comment_replies():
    comment = CommentFactory.create()
    replies = CommentFactory.create_batch(3, page=comment.page, parent=comment)

    # Hidden replies are not retrieved
    hidden_replies = CommentFactory.create_batch(
        3, page=comment.page, parent=comment, is_visible=False
    )

    comment_replies = comments_service.get_comment_replies(comment)

    for comment_reply in comment_replies:
        # The replies are returned for the requested comment
        assert comment_reply in replies
        assert comment_reply not in hidden_replies


def test_get_comment_reply_count():
    comment = CommentFactory.create()
    # No replies are returned for the new comment
    assert comments_service.get_comment_reply_count(comment) == 0

    replies = CommentFactory.create_batch(3, page=comment.page, parent=comment)

    # Hidden replies are not counted
    CommentFactory.create_batch(5, page=comment.page, parent=comment, is_visible=False)

    # The correct number of replies are returned for the requested comment
    assert comments_service.get_comment_reply_count(comment) == len(replies)


@override_settings(USE_TZ=False)
def test_comment_to_dict(news_page):
    comment = CommentFactory.create(page=news_page, content="a new comment")
    replies = CommentFactory.create_batch(3, page=news_page, parent=comment)

    comment_author_profile = comment.author.profile

    comment_dict = comments_service.comment_to_dict(comment)
    replies_dict: list[dict] = [
        comments_service.comment_to_dict(reply) for reply in replies
    ]

    # The correct id is returned
    assert comment_dict["id"] == comment.pk

    # The correct author_name is returned
    assert comment_dict["author_name"] == comment_author_profile.full_name

    # The correct author_url is returned
    assert comment_dict["author_url"] == reverse(
        "profile-view", args=[comment_author_profile.slug]
    )

    # The correct posted/edited date is returned
    assert comment_dict["posted_date"] == comment.posted_date
    assert comment_dict["edited_date"] == comment.edited_date

    # The correct message content is returned
    assert comment_dict["message"] == comment.content

    # show_replies is only true for comments without a parent
    assert comment_dict["show_replies"] == True
    for reply_dict in replies_dict:
        assert reply_dict["show_replies"] == False

    # The correct reply_count is returned
    assert comment_dict["reply_count"] == len(replies)
    for reply_dict in replies_dict:
        assert reply_dict["reply_count"] == 0

    # The replies are returned correctly
    assert sorted(comment_dict["replies"], key=lambda d: d["id"]) == sorted(
        replies_dict, key=lambda d: d["id"]
    )

    # The correct edit_comment_form_url is returned
    assert comment_dict["edit_comment_form_url"] == reverse(
        "interactions:edit-comment-form",
        kwargs={
            "comment_id": comment.pk,
        },
    )

    # The correct edit_comment_cancel_url is returned
    assert comment_dict["edit_comment_cancel_url"] == reverse(
        "interactions:get-comment",
        kwargs={
            "comment_id": comment.pk,
        },
    )

    # The correct reply_comment_form_url is returned
    assert (
        comment_dict["reply_comment_form_url"]
        == reverse(
            "interactions:get-comment",
            kwargs={
                "comment_id": comment.pk,
            },
        )
        + "?show_reply_form=True"
    )

    # The correct reply_comment_url is returned
    assert comment_dict["reply_comment_url"] == reverse(
        "interactions:reply-comment",
        kwargs={
            "comment_id": comment.pk,
        },
    )

    # The correct reply_comment_cancel_url is returned
    assert comment_dict["reply_comment_cancel_url"] == reverse(
        "interactions:get-comment",
        kwargs={
            "comment_id": comment.pk,
        },
    )

    # The correct reply_form_url is returned for non-replies only
    assert comment_dict["reply_form_url"] == reverse(
        "interactions:comment-on-page",
        args=[comment.page.pk],
    )
    for reply_dict in replies_dict:
        assert getattr(reply_dict, "reply_form_url", None) == None


def test_can_reply_comment():
    comment = CommentFactory()
    user = comment.author

    # Can reply to a new comment
    assert comments_service.can_reply_comment(user, comment) == True

    # Test function called with comment_id instead of comment object
    assert comments_service.can_reply_comment(user, comment.id) == True

    reply = CommentFactory.create(
        page=comment.page,
        parent=comment,
    )

    # Can not reply to another reply
    assert comments_service.can_reply_comment(user, reply) == False

    # Test function called with comment_id instead of comment object
    assert comments_service.can_reply_comment(user, reply.id) == False

    # Can not reply to a non-existent comment
    with pytest.raises(AssertionError):
        comments_service.can_reply_comment(user, None)

    # Test function called with invalid comment_id instead of comment object
    with pytest.raises(Comment.DoesNotExist):
        comments_service.can_reply_comment(user, 123456)


@override_settings(USE_TZ=False)
def test_get_page_comments_response(user, news_page):
    comments = CommentFactory.create_batch(5, page=news_page)
    comments_dict = [
        comments_service.comment_to_dict(page_comment)
        for page_comment in comments_service.get_page_comments(news_page)
    ]

    request = RequestFactory().get(path="/")
    request.user = user
    template_response = comments_service.get_page_comments_response(request, news_page)

    # Test response template contains the expected context
    assert template_response.template_name == "dwds/components/comments.html"
    assert template_response.context_data["user"] == user
    assert template_response.context_data["comment_count"] == len(comments)
    assert template_response.context_data["comments"] == comments_dict
    assert isinstance(template_response.context_data["comment_form"], CommentForm)
    assert template_response.context_data["comment_form_url"] == reverse(
        "interactions:comment-on-page", args=[news_page.pk]
    )
    assert template_response.context_data["request"] == request


def test_get_comment_response(user):
    comment = CommentFactory()
    comment_dict = comments_service.comment_to_dict(comment)
    request = RequestFactory().get(path="/")
    request.user = user
    template_response = comments_service.get_comment_response(request, comment)

    # Test response template contains the expected context
    assert template_response.template_name == "dwds/components/comment.html"
    assert template_response.context_data["comment"] == comment_dict
    assert template_response.context_data["request"] == request
    assert template_response.context_data["show_reply_form"] == False
