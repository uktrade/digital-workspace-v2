from django import forms

from peoplefinder.models import TeamMember


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
