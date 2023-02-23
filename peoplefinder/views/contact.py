from django.views.generic import ListView
from django.db.models import Q

from peoplefinder.models import Person, Team
from peoplefinder.services.team import TeamService

from .base import PeoplefinderView


class ContactPeopleView(ListView, PeoplefinderView):
    model = Person
    context_object_name = "people"
    template_name = "peoplefinder/contact-people.html"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        self.team_service = TeamService()
        self.team = None
        self.sub_teams = None

        if team_slug := request.GET.get("team"):
            self.team = Team.objects.get(slug=team_slug)

        if request.GET.get("sub_teams", "true") == "true":
            self.sub_teams = self.team_service.get_all_child_teams(self.team)

    def get_queryset(self):
        qs = Person.active.all().exclude(user=self.request.user)

        team_filter = Q()

        if self.team:
            team_filter = team_filter | Q(roles__team=self.team)

        if self.sub_teams:
            team_filter = team_filter | Q(roles__team__in=self.sub_teams)

        qs = qs.filter(team_filter)

        return qs

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "team": self.team,
            "sub_teams": self.sub_teams,
        }
