from django.urls import path

from dw_design_system import views


urlpatterns = [
    path("styles/", views.styles, name="dwds-styles"),
    path("", views.components, name="dwds-components"),
    path("get/", views.get_component, name="dwds-component-get"),
]
