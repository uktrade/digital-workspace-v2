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
    path("page/<int:pk>/comment", views.comment_on_page, name="comment-on-page"),
    path("comment/<int:pk>/hide", views.hide_comment, name="hide-comment"),
    path(
        "comment/<int:comment_id>/edit",
        views.edit_comment,
        name="edit-comment",
    ),
    path(
        "page/<int:page_id>/comment/<int:comment_id>/edit",
        views.edit_page_comment_form,
        name="edit-page-comment-form",
    ),
    path(
        "page/<int:page_id>/comment/<int:comment_id>/<str:field>/",
        views.page_comment,
        name="page-comment",
    ),
    path(
        "page/<int:page_id>/comment/<int:comment_id>/",
        views.page_comment,
        name="page-comment",
    ),
]
