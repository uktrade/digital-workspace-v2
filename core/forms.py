from django import forms


class PageProblemFoundForm(forms.Form):
    trying_to = forms.CharField(
        label="What were you trying to do?",
        max_length=300,
        widget=forms.TextInput(
            attrs={"class": "govuk-input", }
        )
    )
    what_went_wrong = forms.CharField(
        label='What went wrong?',
        max_length=300,
        widget=forms.TextInput(
            attrs={"class": "govuk-input", }
        )
    )
