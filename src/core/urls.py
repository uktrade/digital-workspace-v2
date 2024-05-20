from django.urls import path

from core import views


urlpatterns = [
    path("problem-found/", views.page_problem_found, name="page_problem_found"),
    path("deactivated/", views.deactivated, name="deactivated"),
    path("report/user-groups", views.user_groups_report, name="user-groups-report"),
    path(
        "report/content-owners/",
        views.content_owners_report,
        name="report_content_owners",
    ),
    path("tag/<slug:slug>", views.tag_index, name="tag-index"),
]
