from django import forms
from django.utils.text import slugify

from peoplefinder.models import Team
from peoplefinder.services.team import TeamService


class TeamForm(forms.ModelForm):
    use_required_attribute = False

    class Meta:
        model = Team
        fields = [
            "name",
            "abbreviation",
            "description",
            "parent_team",
        ]

    parent_team = forms.IntegerField()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.initial.update(
            parent_team=TeamService().get_immediate_parent_team(self.instance)
        )

    def clean(self):
        cleaned_data = super().clean()

        if "parent_team" in self.changed_data:
            try:
                self.new_parent_team = Team.objects.get(pk=cleaned_data["parent_team"])
            except Team.DoesNotExist:
                self.add_error("parent_team", "Invalid parent_team value")

        return cleaned_data

    def save(self, commit=True):
        if "name" in self.changed_data:
            self.instance.slug = slugify(self.cleaned_data["name"])

        super().save(commit=commit)

        if "parent_team" in self.changed_data:
            TeamService().update_team_parent(self.instance, self.new_parent_team)

        return self.instance
