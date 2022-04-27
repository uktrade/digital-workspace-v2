from django import forms


TEAMS_FILTER = "teams"
PEOPLE_FILTER = "people"
SEARCH_FILTERS = [
    (TEAMS_FILTER, "Teams"),
    (PEOPLE_FILTER, "People"),
]


class SearchForm(forms.Form):
    query = forms.CharField(required=False, empty_value=None)
    filters = forms.MultipleChoiceField(
        choices=SEARCH_FILTERS,
        required=False,
        initial=[TEAMS_FILTER, PEOPLE_FILTER],
        widget=forms.CheckboxSelectMultiple(attrs={"class": "govuk-checkboxes__input"}),
    )
