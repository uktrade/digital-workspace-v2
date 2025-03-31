import pytest
from interactions.services import comments as comments_service

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


# TODO: further methods to test
# add_page_comment
# get_page_comments
# get_page_comment_count
# get_comment_replies
# get_comment_reply_count
# comment_to_dict (a little more complex)
