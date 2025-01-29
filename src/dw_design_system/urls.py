from django.http import HttpResponseRedirect
from django.urls import path, reverse

from dw_design_system import views


urlpatterns = [
    path("styles/", views.styles, name="dwds-styles"),
    path("layouts/", views.layouts, name="dwds-layouts"),
    path(
        "",
        lambda request: HttpResponseRedirect(reverse("dwds-components")),
    ),
    path(
        "get/<str:template_type>/",
        views.get_dwds_template,
        name="dwds-template-get",
    ),
    path(
        "content/",
        views.dwds_templates("content"),
        name="dwds-content",
    ),
    path(
        "components/",
        views.dwds_templates("components"),
        name="dwds-components",
    ),
    path(
        "icons/",
        views.dwds_templates("icons"),
        name="dwds-icons",
    ),
]
