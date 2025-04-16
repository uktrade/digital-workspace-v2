from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.generic import DetailView

from peoplefinder.models import Person
from peoplefinder.services.team import TeamService
from peoplefinder.views.base import PeoplefinderView


@method_decorator(xframe_options_sameorigin, name="dispatch")
class OrganogramView(DetailView, PeoplefinderView):
    template_name = "peoplefinder/organogram.html"
    model = Person
    context_object_name = "profile"
    slug_url_kwarg = "profile_slug"

    def get_queryset(self):
        return super().get_queryset().active()

    def get_context_data(self, **kwargs: dict) -> dict:
        context = super().get_context_data(**kwargs)

        profile = context["profile"]
        roles = profile.roles.select_related("team").all()
        context["roles"] = roles
        context["manager"] = profile.manager
        context["manages_profiles"] = self.get_queryset().filter(manager=profile)

        if roles:
            team = roles[0].team
            context["team"] = team
            context["parent_teams"] = list(TeamService().get_all_parent_teams(team)) + [
                team
            ]

        return context
