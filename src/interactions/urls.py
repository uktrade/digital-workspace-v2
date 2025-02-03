from django.urls import path

from . import views


app_name = "interactions"

urlpatterns = [
    path("bookmark", views.bookmark, name="bookmark"),
    path("reaction", views.react_to_page, name="reaction"),
    path("bookmark/<int:pk>/remove", views.remove_bookmark, name="bookmark-remove"),
    path("bookmarks", views.bookmark_index, name="bookmark-index"),
]
