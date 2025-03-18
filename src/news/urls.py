from django.urls import path

from news import views


app_name = "news"

urlpatterns = [
    path(
        "hide-comment/<int:pk>/",
        views.hide_comment,
        name="hide-comment",
    ),
]
