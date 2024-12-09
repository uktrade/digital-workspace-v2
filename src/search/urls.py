from django.urls import path
from django.views.generic import RedirectView

from .views import autocomplete, explore, export_search, search


app_name = "search"

urlpatterns = [
    path(
        "v2/",
        RedirectView.as_view(
            pattern_name="search:home", permanent=True, query_string=True
        ),
    ),
    path(
        "v2/<str:category>/",
        RedirectView.as_view(
            pattern_name="search:category", permanent=True, query_string=True
        ),
    ),
    path("explore/", explore, name="explore"),
    path("export_search/", export_search, name="export_search"),
    path("autocomplete/", autocomplete, name="autocomplete"),
    path("<str:category>/", search, name="category"),
    path("", search, name="home"),
]
