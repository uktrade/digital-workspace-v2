from django.urls import path

from . import views


app_name = "interactions"

urlpatterns = [
    path("bookmark", views.bookmark, name="bookmark"),
    path(
        "comment-reactions/<int:pk>/", views.react_to_comment, name="comment-reactions"
    ),
    path("bookmark/<int:pk>/remove", views.remove_bookmark, name="bookmark-remove"),
    path("bookmarks", views.bookmark_index, name="bookmark-index"),
    path("page/<int:pk>/react", views.react_to_page, name="page-reactions"),
    path("page/<int:pk>/comments", views.get_page_comments, name="get-page-comments"),
    path("page/<int:pk>/comment", views.comment_on_page, name="comment-on-page"),
    path(
        "comment/<int:comment_id>/reply", views.reply_to_comment, name="reply-comment"
    ),
    path("comment/<int:pk>/hide", views.hide_comment, name="hide-comment"),
    path(
        "comment/<int:comment_id>/edit",
        views.edit_comment,
        name="edit-comment",
    ),
    path(
        "comment/<int:comment_id>/edit/form",
        views.edit_comment_form,
        name="edit-comment-form",
    ),
    path(
        "comment/<int:comment_id>/",
        views.get_comment,
        name="get-comment",
    ),
]
