from django.urls import path

from content import views


urlpatterns = [
    path(
        "get-person-roles/<int:person_id>/",
        views.get_person_roles,
        name="get-person-roles",
    )
]
