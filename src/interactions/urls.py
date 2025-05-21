from django.urls import path

from interactions.views import (
    bookmarks,
    comment_reactions,
    comments,
    page_reactions,
    subscriptions,
    tag_subscriptions,
)


app_name = "interactions"

urlpatterns = [
    path(
        "comment-reactions/<int:pk>/",
        comment_reactions.react_to_comment,
        name="comment-reactions",
    ),
    # path("comment-reactions/<int:pk>/users", comment_reactions.get_comment_reaction_users, name="comment-reactions-users"),
    path("bookmark", bookmarks.bookmark, name="bookmark"),
    path("bookmark/<int:pk>/remove", bookmarks.remove_bookmark, name="bookmark-remove"),
    path("bookmarks", bookmarks.bookmark_index, name="bookmark-index"),
    path("page/<int:pk>/react", page_reactions.react_to_page, name="page-reactions"),
    path(
        "page/<int:pk>/page-reaction-users",
        page_reactions.get_page_reaction_users,
        name="page-reaction-users",
    ),
    path(
        "comment/<int:pk>/comment-reaction-users",
        comment_reactions.get_comment_reaction_users,
        name="comment-reaction-users",
    ),
    path(
        "page/<int:pk>/comments", comments.get_page_comments, name="get-page-comments"
    ),
    path("page/<int:pk>/comment", comments.comment_on_page, name="comment-on-page"),
    path(
        "comment/<int:comment_id>/reply",
        comments.reply_to_comment,
        name="reply-comment",
    ),
    path("comment/<int:pk>/hide", comments.hide_comment, name="hide-comment"),
    path(
        "comment/<int:comment_id>/edit",
        comments.edit_comment,
        name="edit-comment",
    ),
    path(
        "comment/<int:comment_id>/edit/form",
        comments.edit_comment_form,
        name="edit-comment-form",
    ),
    path(
        "comment/<int:comment_id>/",
        comments.get_comment,
        name="get-comment",
    ),
    path(
        "tag/<int:tag_pk>/subscribe/",
        tag_subscriptions.subscribe,
        name="subscribe-to-tag",
    ),
    path(
        "tag/<int:tag_pk>/unsubscribe/",
        tag_subscriptions.unsubscribe,
        name="unsubscribe-from-tag",
    ),
    path(
        "manage-subscriptions/",
        subscriptions.manage_subscriptions,
        name="manage_subscriptions",
    ),
]
