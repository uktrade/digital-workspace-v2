from django.urls import path

from peoplefinder.views.home import PeopleHome, TeamHome
from peoplefinder.views.profile import ProfileDetailView, ProfileEditView
from peoplefinder.views.team import TeamDetailView, TeamPeopleView, TeamTreeView


people_urlpatterns = [
    path("", PeopleHome.as_view(), name="people-home"),
    path("<pk>/", ProfileDetailView.as_view(), name="profile-view"),
    path("<pk>/edit", ProfileEditView.as_view(), name="profile-edit"),
]

teams_urlpatterns = [
    path("", TeamHome.as_view(), name="team-home"),
    path("<slug>/", TeamDetailView.as_view(), name="team-view"),
    path("<slug>/tree", TeamTreeView.as_view(), name="team-tree"),
    path("<slug>/people", TeamPeopleView.as_view(), name="team-people"),
]
