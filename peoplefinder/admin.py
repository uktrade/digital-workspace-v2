from django.contrib import admin

from core.admin import admin_site
from peoplefinder.forms.admin import TeamModelForm
from peoplefinder.models import LegacyAuditLog, Person, Team, TeamMember
from peoplefinder.services.team import TeamService


class LegacyAuditLogModelAdmin(admin.ModelAdmin):
    """Admin page for the LegacyAuditLog model."""

    list_display = ["actor", "action", "content_type", "content_object"]
    list_filter = [
        "action",
        ("content_type", admin.RelatedOnlyFieldListFilter),
    ]
    search_fields = [
        "actor__first_name",
        "actor__last_name",
        "actor__email",
    ]


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
                team_service.team_updated(obj, request.user)
        else:
            team_service.add_team(obj, new_parent_team)
            team_service.team_created(obj, request.user)


admin_site.register(LegacyAuditLog, LegacyAuditLogModelAdmin)
admin_site.register(Person, admin.ModelAdmin)
admin_site.register(Team, TeamModelAdmin)
admin_site.register(TeamMember, admin.ModelAdmin)
