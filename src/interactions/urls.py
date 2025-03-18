from django.urls import path

from . import views


app_name = "interactions"

urlpatterns = [
    path("bookmark", views.bookmark, name="bookmark"),
    path("reactions/<int:pk>/", views.react_to_page, name="reactions"),
    path("bookmark/<int:pk>/remove", views.remove_bookmark, name="bookmark-remove"),
    path("bookmarks", views.bookmark_index, name="bookmark-index"),
    path("comment/<int:pk>/", views.comment_on_page, name="comment-on-page"),
]
