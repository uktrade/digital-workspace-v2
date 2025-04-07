import pytest
from interactions.services import comments as comments_service
from news.models import Comment

pytestmark = pytest.mark.django_db


def test_show_comment(comment):
    comment.is_visible = False
    comments_service.show_comment(comment)
    comment.refresh_from_db()
    assert comment.is_visible == True


def test_hide_comment(comment):
    assert comment.is_visible == True
    comments_service.hide_comment(comment)
    comment.refresh_from_db()
    assert comment.is_visible == False


def test_can_hide_comment(user, user2, comment):
    # The user is the author of the comment
    assert comments_service.can_hide_comment(user, comment) == True

    # The user is not the author of the comment
    assert comments_service.can_hide_comment(user2, comment) == False

    # Test function called with comment_id instead of comment object
    assert comments_service.can_hide_comment(user, comment.id) == True


def test_edit_comment(comment):
    edited_content = "edited content of comment"
    comments_service.edit_comment(comment.id, edited_content)
    comment.refresh_from_db()
    assert comment.content == edited_content
    assert comment.edited_date is not None


def test_can_edit_comment(user, user2, comment):
    # The user is the author of the comment
    assert comments_service.can_edit_comment(user, comment) == True

    # The user is not the author of the comment
    assert comments_service.can_edit_comment(user2, comment) == False

    # Test function called with comment_id instead of comment object
    assert comments_service.can_edit_comment(user, comment.id) == True


def test_add_page_comment(news_page, user, user2):
    comment_content = "A new comment"
    comment = comments_service.add_page_comment(news_page, user, comment_content, None)

    # The comment is created succesfully
    assert isinstance(comment, Comment)
    assert comment.content == comment_content

    reply_content = "A comment reply"
    reply = comments_service.add_page_comment(
        news_page, user2, reply_content, comment.pk
    )

    # The comment reply is created succesfully
    assert isinstance(reply, Comment)
    assert reply.content == reply_content
    assert reply.parent == comment


def test_get_page_comments(news_page, news_page2, comment_factory):
    comment_1 = comment_factory(page=news_page)
    comment_2 = comment_factory(page=news_page)
    comment_3 = comment_factory(page=news_page2)
    comments = comments_service.get_page_comments(news_page)

    # The comments are returned for the requested page
    assert comment_1 in comments
    assert comment_2 in comments
    assert comment_3 not in comments


def test_get_page_comment_count(news_page, comment_factory):
    comment_factory(page=news_page)
    comment_factory(page=news_page)

    # The comment count is returned for the requested page
    assert comments_service.get_page_comment_count(news_page) == 2


def test_get_comment_replies(comment, comment_factory):
    reply_1 = comment_factory(parent=comment)
    reply_2 = comment_factory(parent=comment)

    replies = comments_service.get_comment_replies(comment)

    # The replies are returned for the requested comment
    assert reply_1 in replies
    assert reply_2 in replies


# TODO: further methods to test
# get_comment_replies
# get_comment_reply_count
# comment_to_dict (a little more complex)
# can_reply_comment
