from django.contrib import admin

from core.admin import admin_site
from peoplefinder.forms import TeamModelForm
from peoplefinder.models import Person, Team, TeamMember
from peoplefinder.services.team import TeamService


class TeamModelAdmin(admin.ModelAdmin):
    """Admin page for the Team model."""

    form = TeamModelForm

    def save_model(self, request, obj, form, change):  # type: ignore
        """Save the model and update the team hierarchy."""
        super().save_model(request, obj, form, change)

        team_service = TeamService()

        current_parent_team = team_service.get_immediate_parent_team(obj)
        new_parent_team = form.cleaned_data["parent_team"]

        if change:
            if current_parent_team != new_parent_team:
                team_service.update_team_parent(obj, new_parent_team)
        else:
            team_service.add_team(obj, new_parent_team)


admin_site.register(Person, admin.ModelAdmin)
admin_site.register(Team, TeamModelAdmin)
admin_site.register(TeamMember, admin.ModelAdmin)
