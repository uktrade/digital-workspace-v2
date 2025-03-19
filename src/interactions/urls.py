from django.urls import path

from . import views


app_name = "interactions"

urlpatterns = [
    path("bookmark", views.bookmark, name="bookmark"),
    path("bookmark/<int:pk>/remove", views.remove_bookmark, name="bookmark-remove"),
    path("bookmarks", views.bookmark_index, name="bookmark-index"),
    path("page/<int:pk>/react", views.react_to_page, name="reactions"),
    path("page/<int:pk>/comment", views.comment_on_page, name="comment-on-page"),
    path("comment/<int:pk>/hide", views.hide_comment, name="hide-comment"),
]
