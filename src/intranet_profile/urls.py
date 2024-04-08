from django.urls import path

from . import views

app_name = "profile"

urlpatterns = [
    path("bookmark", views.bookmark, name="bookmark"),
]
