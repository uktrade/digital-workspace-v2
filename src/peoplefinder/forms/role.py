from django import forms

from peoplefinder.forms.crispy_helper import RoleFormsetFormHelper
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
            "DELETE",
        ]
        widgets = {
            "person": forms.HiddenInput(),
            "DELETE": forms.HiddenInput(),
        }

    DELETE = forms.BooleanField(
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["team"].label = ""
        self.fields["job_title"].label = ""

    def clean(self):
        cleaned_data = super().clean()

        team_service = TeamService()
        root_team = team_service.get_root_team()

        # Someone is trying to set a new head of the DIT.
        if (
            cleaned_data.get("team") == root_team
            and cleaned_data.get("head_of_team") is True
        ):
            # If there already is one, don't let them do it.
            if (
                root_team.members.active()
                .exclude(id=self.instance.id)
                .filter(head_of_team=True)
                .exists()
            ):
                self.add_error(None, f"There is already a head of the {root_team}")

        return cleaned_data


class RoleFormsetForm(RoleForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = RoleFormsetFormHelper()
