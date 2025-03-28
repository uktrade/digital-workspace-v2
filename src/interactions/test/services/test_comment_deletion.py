import pytest
from interactions.services import comments as comments_service

pytestmark = pytest.mark.django_db


def test_show_comment(comment):
    comment.is_visible = False
    comments_service.show_comment(comment)

    assert comment.is_visible == True


def test_hide_comment(comment):
    assert comment.is_visible == True
    comments_service.hide_comment(comment)
    assert comment.is_visible == False


def test_can_hide_comment(user, user2, comment):
    # The user is the author of the comment
    assert comments_service.can_hide_comment(user, comment) == True

    # The user is not the author of the comment
    assert comments_service.can_hide_comment(user2, comment) == False

    # Test function called with comment_id instead of comment object
    assert comments_service.can_hide_comment(user, comment.id) == True
