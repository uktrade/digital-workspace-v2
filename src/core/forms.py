from django import forms
from wagtail.users.forms import UserEditForm


class PageProblemFoundForm(forms.Form):
    # Maximum URL length discussion https://stackoverflow.com/a/417184.
    page_url = forms.URLField(
        max_length=2000, widget=forms.HiddenInput(), required=True
    )
    trying_to = forms.CharField(
        label="What were you trying to do?",
        max_length=500,
        widget=forms.Textarea(
            attrs={
                "class": "govuk-textarea",
            }
        ),
    )
    what_went_wrong = forms.CharField(
        label="What went wrong?",
        max_length=500,
        widget=forms.Textarea(
            attrs={
                "class": "govuk-textarea",
            }
        ),
    )


class WagtailUserEditForm(UserEditForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "is_superuser" in self.fields:
            del self.fields["is_superuser"]
