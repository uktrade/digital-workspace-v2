from typing import Any, Dict

from django import forms

from peoplefinder.models import Team
from peoplefinder.services.team import TeamService


class TeamModelForm(forms.ModelForm):
    """Form for the team model admin page."""

    class Meta:
        model = Team
        fields = "__all__"

    parent_team = forms.ModelChoiceField(Team.objects.all(), required=False)

    def __init__(
        self,
        *args: tuple,
        initial: Dict[str, Any] = None,
        instance: Team = None,
        **kwargs: dict,
    ) -> None:
        """Initialise the form with the correct parent team."""
        if not initial:
            initial = {}

        team = instance

        initial["parent_team"] = None

        if team:
            initial["parent_team"] = TeamService().get_immediate_parent_team(team)

        super().__init__(*args, initial=initial, instance=instance, **kwargs)
