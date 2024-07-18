from django.urls import path

from dw_design_system import views


urlpatterns = [
    path("", views.components, name="dwds-components"),
    path("get/", views.get_component, name="dwds-component-get"),
]
