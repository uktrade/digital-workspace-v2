import pytest
from interactions.services import comments as comments_service
from news.models import Comment
from news.factories import CommentFactory, NewsPageFactory
from django.urls import reverse

from peoplefinder.services.person import PersonService
from peoplefinder.test.factories import PersonFactory


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
    comment = CommentFactory.create()
    news_page_comments = comments_service.get_page_comments(news_page)

    for news_comment in news_comments:
        # The comments are returned for the requested page
        assert news_comment in news_page_comments

    # Comments on other pages are not returned
    assert comment not in news_page_comments


def test_get_page_comment_count(news_page):
    comments = CommentFactory.create_batch(3, page=news_page)

    # The comment count is returned for the requested page
    assert comments_service.get_page_comment_count(news_page) == len(comments)


def test_get_comment_replies():
    comment = CommentFactory.create()
    replies = CommentFactory.create_batch(3, page=comment.page, parent=comment)
    comment_replies = comments_service.get_comment_replies(comment)

    for reply in replies:
        # The replies are returned for the requested comment
        assert reply in comment_replies


def test_get_comment_reply_count():
    comment = CommentFactory.create()
    # No replies are returned for the new comment
    assert comments_service.get_comment_reply_count(comment) == 0

    replies = CommentFactory.create_batch(3, page=comment.page, parent=comment)

    # The correct number of replies are returned for the requested comment
    assert comments_service.get_comment_reply_count(comment) == len(replies)


# @pytest.mark.skip(reason="Missing user profile setup")
def test_comment_to_dict(news_page):
    comment = CommentFactory.create(page=news_page, content="a new comment")
    replies = CommentFactory.create_batch(3, page=news_page, parent=comment)

    # TODO: Fix user profile creation
    # PersonService().create_user_profile(user=comment.author)
    PersonFactory.create(user=comment.author)
    comment.refresh_from_db()
    # call_command("create_user_profiles")
    comment_author_profile = comment.author.profile
    assert comment_author_profile
    comment_dict = comments_service.comment_to_dict(comment)
    replies_dict: list[dict] = [
        comments_service.comment_to_dict(reply) for reply in replies
    ]

    # The correct id is returned
    assert comment_dict["id"] == comment.id

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
    for reply in comment_dict["replies"]:
        assert reply in replies_dict

    # in_reply_to returns the correct parent comment id
    assert comment_dict["in_reply_to"] == None
    for reply_dict in replies_dict:
        assert reply_dict["in_reply_to"] == comment.id

    # The correct edit_comment_form_url is returned
    assert comment_dict["edit_comment_form_url"] == reverse(
        "interactions:edit-comment-form",
        kwargs={
            "comment_id": comment.id,
        },
    )

    # The correct edit_comment_cancel_url is returned
    assert comment_dict["edit_comment_cancel_url"] == reverse(
        "interactions:get-comment",
        kwargs={
            "comment_id": comment.id,
        },
    )

    # The correct reply_comment_form_url is returned
    assert (
        comment_dict["reply_comment_form_url"]
        == reverse(
            "interactions:get-comment",
            kwargs={
                "comment_id": comment.id,
            },
        )
        + "?show_reply_form=True"
    )

    # The correct reply_comment_url is returned
    assert comment_dict["reply_comment_url"] == reverse(
        "interactions:reply-comment",
        kwargs={
            "comment_id": comment.id,
        },
    )

    # The correct reply_comment_cancel_url is returned
    assert comment_dict["reply_comment_cancel_url"] == reverse(
        "interactions:get-comment",
        kwargs={
            "comment_id": comment.id,
        },
    )

    # The correct reply_form_url is returned for replies only
    assert comment_dict["reply_form_url"] == None
    for reply_dict in replies_dict:
        assert reply_dict["reply_form_url"] == reverse(
            "interactions:edit-comment-form",
            kwargs={
                "comment_id": comment.id,
            },
        )


def test_can_reply_comment():
    comment = CommentFactory.create()
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
    assert comments_service.can_reply_comment(user, 123456) == False


@pytest.mark.skip(reason="TODO, create mock request")
def test_get_page_comments_response(news_page, mocker):
    comments = CommentFactory.create_batch(5, page=news_page)
    request = mocker.Mock()


@pytest.mark.skip(reason="TODO, create mock request")
def test_get_comment_response(news_page, mocker):
    comment = CommentFactory.create()
    request = mocker.Mock()
