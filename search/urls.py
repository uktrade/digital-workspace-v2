from django.urls import path

from . import views

app_name = "search"
urlpatterns = [
    path("", views.search_global, name="search_global"),
    path("information/", views.search_wordpress, name="search_wordpress")
]
