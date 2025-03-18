from django.urls import path

from . import views


app_name = "interactions"

urlpatterns = [
    path("bookmark", views.bookmark, name="bookmark"),
    path("reactions/<int:pk>/", views.react_to_page, name="reactions"),
    path("bookmark/<int:pk>/remove", views.remove_bookmark, name="bookmark-remove"),
    path("bookmarks", views.bookmark_index, name="bookmark-index"),
    path("edit-comment/<int:pk>/", views.edit_comment, name="edit-comment"),
    path(
        "edit-comment-form/<int:pk>/", views.edit_comment_form, name="edit-comment-form"
    ),
]
