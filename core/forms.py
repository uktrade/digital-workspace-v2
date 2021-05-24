from django import forms


class PageProblemFoundForm(forms.Form):
    trying_to = forms.CharField(
        label="What were you trying to do?",
        max_length=500,
        widget=forms.Textarea(
            attrs={"class": "govuk-textarea", }
        )
    )
    what_went_wrong = forms.CharField(
        label='What went wrong?',
        max_length=500,
        widget=forms.Textarea(
            attrs={"class": "govuk-textarea", }
        )
    )
