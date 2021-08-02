from django.urls import include, path

from peoplefinder.views.home import PeopleHome, TeamHome
from peoplefinder.views.manager import (
    ManagerCancel,
    ManagerSearch,
    ManagerSelect,
    ManagerUpdate,
)
from peoplefinder.views.profile import (
    ProfileDetailView,
    ProfileEditView,
    ProfileLeavingDitView,
)
from peoplefinder.views.role import RoleFormView, TeamSelectView
from peoplefinder.views.team import (
    TeamAddNewSubteamView,
    TeamDetailView,
    TeamEditView,
    TeamPeopleOutsideSubteamsView,
    TeamPeopleView,
    TeamTreeView,
)


people_urlpatterns = [
    path("", PeopleHome.as_view(), name="people-home"),
    path("<int:profile_pk>/", ProfileDetailView.as_view(), name="profile-view"),
    path("<int:profile_pk>/edit/", ProfileEditView.as_view(), name="profile-edit"),
    # Manager component
    path(
        "<int:profile_pk>/edit/manager/",
        include(
            [
                path(
                    "select/<int:user_pk>",
                    ManagerSelect.as_view(),
                    name="profile-edit-manager-select",
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
    # Roles
    path("<int:profile_pk>/edit/roles/", RoleFormView.as_view(), name="roles"),
    path(
        "<int:profile_pk>/edit/roles/<int:role_pk>/",
        RoleFormView.as_view(),
        name="role",
    ),
    # Leaving DIT
    path(
        "<int:profile_pk>/leaving-dit",
        ProfileLeavingDitView.as_view(),
        name="profile-leaving-dit",
    ),
]

teams_urlpatterns = [
    path("", TeamHome.as_view(), name="team-home"),
    path("<slug>/", TeamDetailView.as_view(), name="team-view"),
    path("<slug>/edit", TeamEditView.as_view(), name="team-edit"),
    path("<slug>/tree", TeamTreeView.as_view(), name="team-tree"),
    path("<slug>/people", TeamPeopleView.as_view(), name="team-people"),
    path(
        "<slug>/people-outside-subteams",
        TeamPeopleOutsideSubteamsView.as_view(),
        name="team-people-outside-subteams",
    ),
    path(
        "<slug>/add-new-subteam",
        TeamAddNewSubteamView.as_view(),
        name="team-add-new-subteam",
    ),
]

api_urlpatterns = [
    path("team-select", TeamSelectView.as_view(), name="team-select"),
]
