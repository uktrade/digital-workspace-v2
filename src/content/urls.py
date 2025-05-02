from django.urls import path

from content import views


urlpatterns = [
    path("get-user-roles/<int:person_id>/", views.get_user_roles, name="get-user-roles")
]
