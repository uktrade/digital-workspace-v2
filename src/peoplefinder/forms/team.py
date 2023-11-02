from django import forms

from peoplefinder.models import Team
from peoplefinder.services.team import TeamService, TeamServiceError


class TeamForm(forms.ModelForm):
    use_required_attribute = False

    class Meta:
        model = Team
        fields = [
            "name",
            "abbreviation",
            "description",
            "parent_team",
            "leaders_ordering",
            "leaders_positions",
        ]

    parent_team = forms.IntegerField()
    # Example: "23,56,34"
    leaders_positions = forms.CharField(required=False, empty_value=None)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.team_service = TeamService()

        # creating a new team
        # `_state.adding` is safer than pk/id check as that doesn't work for uuids with
        # a default value
        # https://docs.djangoproject.com/en/3.2/ref/models/instances/#other-attributes
        self.creating = self.instance._state.adding
        # editing an existing team
        self.editing = not self.creating

        if self.editing:
            parent_team = self.team_service.get_immediate_parent_team(self.instance)

            # parent_team will be None if the root team is being edited.
            if parent_team:
                self.initial.update(parent_team=parent_team.pk)

        self.is_root_team = self.team_service.get_root_team() == self.instance

        # parent_team is not required if we are editing the root team
        if self.is_root_team:
            self.fields["parent_team"].required = False

    def clean_leaders_positions(self):
        leaders_positions = self.cleaned_data["leaders_positions"]

        if not leaders_positions:
            return None

        return list(map(int, leaders_positions.split(",")))

    def clean_description(self):
        # Some really dumb validation to prevent XSS with 'javascript:' urls
        description = self.cleaned_data["description"]
        if "javascript:" in description:
            raise forms.ValidationError(
                "You cannot use 'javascript:' in the description"
            )
        if "data:" in description:
            raise forms.ValidationError("You cannot use 'data:' in the description")
        return description

    def clean(self):
        cleaned_data = super().clean()

        self.new_parent_team = None

        if cleaned_data["parent_team"]:
            try:
                self.new_parent_team = Team.objects.get(pk=cleaned_data["parent_team"])
            except Team.DoesNotExist:
                self.add_error("parent_team", "Invalid parent team")

        if (
            self.editing
            and ("parent_team" in self.changed_data)
            and self.new_parent_team
        ):
            try:
                self.team_service.validate_team_parent_update(
                    self.instance, self.new_parent_team
                )
            except TeamServiceError as e:
                self.add_error("parent_team", str(e))

        return cleaned_data

    def save(self, commit=True):
        super().save(commit=commit)

        if self.creating:
            self.team_service.add_team(self.instance, self.new_parent_team)
        # editing and...
        elif "parent_team" in self.changed_data:
            self.team_service.update_team_parent(self.instance, self.new_parent_team)

        # This depends on the team's parent so it has to happen after we update the team
        # tree.
        if "name" in self.changed_data:
            self.instance.slug = self.team_service.generate_team_slug(self.instance)
            self.instance.save()

        return self.instance
