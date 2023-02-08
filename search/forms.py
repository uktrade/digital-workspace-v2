from django import forms
from django.db.models import TextChoices


class SearchCategory(TextChoices):
    PAGES = "pages"
    TEAMS = "teams"
    PEOPLE = "people"


class SearchForm(forms.Form):
    query = forms.CharField(required=False, empty_value=None)
    category = forms.ChoiceField(choices=SearchCategory.choices, required=False)
