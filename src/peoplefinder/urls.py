from django.urls import include, path
from rest_framework import routers

from peoplefinder.views.activity_stream import ActivityStreamViewSet
from peoplefinder.views.api.person import PersonViewSet
from peoplefinder.views.api.team import TeamView
from peoplefinder.views.directory import PeopleDirectory, discover
from peoplefinder.views.home import PeopleHome, TeamHome
from peoplefinder.views.manager import (
    ManagerCancel,
    ManagerClear,
    ManagerSearch,
    ManagerSelect,
    ManagerUpdate,
)
from peoplefinder.views.profile import (
    DeleteConfirmationView,
    ProfileActivateAction,
    ProfileConfirmDetailsView,
    ProfileDeleteView,
    ProfileDetailView,
    ProfileEditView,
    ProfileLeavingDbtView,
    ProfileLegacyView,
    ProfileUpdateUserView,
    get_profile_by_staff_sso_id,
    get_profile_card,
    profile_edit_blank_teams_form,
    redirect_to_profile_edit,
)
from peoplefinder.views.role import TeamSelectView
from peoplefinder.views.team import (
    TeamAddNewSubteamView,
    TeamDeleteView,
    TeamDetailView,
    TeamEditView,
    TeamTreeView,
)
from peoplefinder.views.organogram import OrganogramView


people_urlpatterns = [
    path("", PeopleHome.as_view(), name="people-home"),
    path("directory/", PeopleDirectory.as_view(), name="people-directory"),
    path("discover/", discover, name="discover"),
    path(
        "delete-confirmation/",
        DeleteConfirmationView.as_view(),
        name="delete-confirmation",
    ),
    path("<uuid:profile_slug>/", ProfileDetailView.as_view(), name="profile-view"),
    path(
        "<profile_legacy_slug>/",
        ProfileLegacyView.as_view(),
        name="profile-legacy-view",
    ),
    # designed to be viewed inside an iframe
    path(
        "<uuid:profile_slug>/organogram/",
        OrganogramView.as_view(),
        name="organogram-person",
    ),

    # Redirects to profile-edit-section with edit_section=personal
    path(
        "<uuid:profile_slug>/blank-teams-form/",
        profile_edit_blank_teams_form,
        name="profile-edit-blank-teams-form",
    ),
    # Redirects to profile-edit-section with edit_section=personal
    path(
        "<uuid:profile_slug>/edit/",
        redirect_to_profile_edit,
        name="profile-edit",
    ),
    # Manager component
    path(
        "<uuid:profile_slug>/edit/manager/",
        include(
            [
                path(
                    "select/<uuid:manager_slug>",
                    ManagerSelect.as_view(),
                    name="profile-edit-manager-select",
                ),
                path(
                    "clear/",
                    ManagerClear.as_view(),
                    name="profile-edit-manager-clear",
                ),
                path(
                    "update",
                    ManagerUpdate.as_view(),
                    name="profile-edit-manager-update",
                ),
                path(
                    "cancel",
                    ManagerCancel.as_view(),
                    name="profile-edit-manager-cancel",
                ),
                path(
                    "search",
                    ManagerSearch.as_view(),
                    name="profile-edit-manager-search",
                ),
            ]
        ),
    ),
    # Edit sections
    path(
        "<uuid:profile_slug>/edit/<str:edit_section>/",
        ProfileEditView.as_view(),
        name="profile-edit-section",
    ),
    # Leaving DBT
    path(
        "<uuid:profile_slug>/leaving-dbt",
        ProfileLeavingDbtView.as_view(),
        name="profile-leaving-dit",
    ),
    path(
        "<uuid:profile_slug>/delete/",
        ProfileDeleteView.as_view(),
        name="profile-delete",
    ),
    # Confirm details
    path(
        "<uuid:profile_slug>/confirm-details/",
        ProfileConfirmDetailsView.as_view(),
        name="profile-confirm-details",
    ),
    # Activate
    path(
        "<uuid:profile_slug>/activate/",
        ProfileActivateAction.as_view(),
        name="profile-activate",
    ),
    # Update profile user
    path(
        "<uuid:profile_slug>/update-user/",
        ProfileUpdateUserView.as_view(),
        name="profile-update-user",
    ),
    path(
        "<str:staff_sso_email_user_id>/card",
        get_profile_card,
        name="profile-get-card",
    ),
    path(
        "get-by-staff-sso-id/<str:staff_sso_id>/",
        get_profile_by_staff_sso_id,
        name="profile-get-by-staff-sso-id",
    ),
]

teams_urlpatterns = [
    path("", TeamHome.as_view(), name="team-home"),
    path("<slug>/", TeamDetailView.as_view(), name="team-view"),
    path("<slug>/edit", TeamEditView.as_view(), name="team-edit"),
    path("<slug>/delete", TeamDeleteView.as_view(), name="team-delete"),
    path("<slug>/tree", TeamTreeView.as_view(), name="team-tree"),
    path(
        "<slug>/add-new-subteam",
        TeamAddNewSubteamView.as_view(),
        name="team-add-new-subteam",
    ),
]

router = routers.DefaultRouter()
router.register(
    "activity-stream", ActivityStreamViewSet, basename="activity-stream-people"
)
router.register("person-api", PersonViewSet, basename="person-api-people")
router.register("team-api", TeamView, basename="team-api-teams")

api_urlpatterns = [
    path("", include(router.urls)),
    path("team-select", TeamSelectView.as_view(), name="team-select"),
]
