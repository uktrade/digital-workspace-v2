from django.urls import path

from core import views


urlpatterns = [
    path("problem-found/", views.page_problem_found, name="page_problem_found"),
    path("deactivated/", views.deactivated, name="deactivated"),
    path("400/<exception>/", views.view_400),
    path("403/<exception>/", views.view_403),
    path("404/<exception>/", views.view_404),
    path("500/", views.view_500),
]
