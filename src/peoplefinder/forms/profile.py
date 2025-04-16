from typing import Set

from django import forms
from django.contrib.auth import get_user_model
from django.core.validators import ValidationError


User = get_user_model()


class GovUkRadioSelect(forms.RadioSelect):
    template_name = "peoplefinder/widgets/radio.html"
    option_template_name = "peoplefinder/widgets/radio_option.html"

    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        option = super().create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )
        option["attrs"]["class"] = "govuk-radios__input"
        return option


class GroupedModelChoiceIterator(forms.models.ModelChoiceIterator):
    def __init__(self, field: "GroupedModelChoiceField") -> None:
        super().__init__(field)
        self.group_field: str = field.group_field

    def __iter__(self):
        if self.field.empty_label is not None:
            yield ("", self.field.empty_label)

        queryset = self.queryset
        groups = sorted(set(queryset.values_list(self.group_field, flat=True)))
        output = []
        for group in groups:
            group_queryset = queryset.filter(**{self.group_field: group})
            output.append((group, [self.choice(obj) for obj in group_queryset]))

        yield from output


class GroupedModelChoiceField(forms.ModelChoiceField):
    iterator = GroupedModelChoiceIterator
    group_field = None
    groups: Set[str] = set()

    def __init__(
        self,
        *args,
        group_field: str,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.group_field = group_field


class ProfileLeavingDbtForm(forms.Form):
    comment = forms.CharField(
        label="My comments",
        help_text="for example, leaving date",
        widget=forms.Textarea(attrs={"class": "govuk-textarea"}),
    )


class ProfileUpdateUserForm(forms.Form):
    username = forms.CharField(required=True)

    def __init__(self, *args, profile, **kwargs):
        super().__init__(*args, **kwargs)

        self.profile = profile

        self.fields["username"].widget.attrs.update(
            {"class": "govuk-input govuk-!-width-one-half"}
        )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")

        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                raise ValidationError("User does not exist")

            if user == self.profile.user:
                raise ValidationError("User is already associated to this profile")

        return cleaned_data
