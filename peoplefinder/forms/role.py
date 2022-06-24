from django import forms

from peoplefinder.models import TeamMember
from peoplefinder.services.team import TeamService


class RoleForm(forms.ModelForm):
    class Meta:
        model = TeamMember
        fields = [
            "person",
            "team",
            "job_title",
            "head_of_team",
        ]
        widgets = {"person": forms.HiddenInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["team"].widget.attrs.update(
            {"class": "govuk-select govuk-!-width-one-half"}
        )
        self.fields["job_title"].widget.attrs.update(
            {"class": "govuk-input govuk-!-width-one-half"}
        )
        self.fields["head_of_team"].widget.attrs.update(
            {"class": "govuk-checkboxes__input"}
        )

    def clean(self):
        cleaned_data = super().clean()

        team_service = TeamService()
        root_team = team_service.get_root_team()

        # Someone is trying to set a new head of the DIT.
        if cleaned_data["team"] == root_team and cleaned_data["head_of_team"] is True:
            # If there already is one, don't let them do it.
            if root_team.members.filter(head_of_team=True).exists():
                self.add_error(None, f"There is already a head of the {root_team}")

        return cleaned_data
