from django.urls import path
from django.views.generic import RedirectView

from .views import search


app_name = "search"

urlpatterns = [
    path("v2/", RedirectView.as_view(
        pattern_name='search:home',
        permanent=True,
        query_string=True
    )),
    path("v2/<str:category>/", RedirectView.as_view(
        pattern_name='search:category',
        permanent=True,
        query_string=True
    )),
    path("", search, name="home"),
    path("<str:category>", search, name="category"),
]
