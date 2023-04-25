from django.urls import path

from .views import home_view, search_v2, toggle_search_v2


app_name = "search"

# TODO[DWPF-454] remove the /v2 segments
# TODO[DWPF-454] implement a redirect from old URL patterns to new ones?
urlpatterns = [
    path("v2/", home_view, name="home"),
    path("v2/<str:category>", search_v2, name="category"),
    # TODO[DWPF-454] remove this URL
    path("v2/toggle/<str:use_v2>", toggle_search_v2, name="toggle"),
]
