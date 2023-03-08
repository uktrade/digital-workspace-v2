from django.urls import path

from .views import v2_search_category, v2_search_all, home_view, toggle_search_v2


app_name = "search"

urlpatterns = [
    path("v2/", home_view, name="home"),
    path("v2/all", v2_search_all, name="all"),
    path("v2/toggle/<str:use_v2>", toggle_search_v2, name="toggle"),
    path("v2/<str:category>", v2_search_category, name="category"),
]
