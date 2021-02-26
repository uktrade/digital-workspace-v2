from django import forms

from peoplefinder.models import Person


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = [
            "first_name",
            "last_name",
            "pronouns",
            "email",
            "contact_email",
            "primary_phone_number",
            "secondary_phone_number",
            "country",
            "town_city_or_region",
            "building",
            "regional_building",
            "international_building",
            "location_in_building",
            "workdays",
        ]
        widgets = {"workdays": forms.CheckboxSelectMultiple}

    first_name = forms.CharField()
    last_name = forms.CharField()
    email = forms.EmailField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        person = self.instance

        self.fields["first_name"].widget.attrs.update(
            {"class": "govuk-input govuk-!-width-one-half", "readonly": "true"}
        )
        self.fields["last_name"].widget.attrs.update(
            {"class": "govuk-input govuk-!-width-one-half", "readonly": "true"}
        )
        self.fields["pronouns"].widget.attrs.update(
            {"class": "govuk-input govuk-!-width-one-half"}
        )
        self.fields["email"].widget.attrs.update(
            {"class": "govuk-input govuk-!-width-one-half", "readonly": "true"}
        )
        self.fields["contact_email"].widget.attrs.update(
            {"class": "govuk-input govuk-!-width-one-half"}
        )
        self.fields["primary_phone_number"].widget.attrs.update(
            {"class": "govuk-input govuk-!-width-one-half"}
        )
        self.fields["secondary_phone_number"].widget.attrs.update(
            {"class": "govuk-input govuk-!-width-one-half"}
        )
        self.fields["country"].widget.attrs.update(
            {"class": "govuk-select govuk-!-width-one-half"}
        )
        self.fields["town_city_or_region"].widget.attrs.update(
            {"class": "govuk-input govuk-!-width-one-half"}
        )
        self.fields["building"].widget.attrs.update(
            {"class": "govuk-input govuk-!-width-one-half"}
        )
        self.fields["regional_building"].widget.attrs.update(
            {"class": "govuk-input govuk-!-width-one-half"}
        )
        self.fields["international_building"].widget.attrs.update(
            {"class": "govuk-input govuk-!-width-one-half"}
        )
        self.fields["location_in_building"].widget.attrs.update(
            {"class": "govuk-input govuk-!-width-one-half"}
        )
        self.fields["workdays"].widget.attrs.update(
            {"class": "govuk-checkboxes__input"}
        )

        self.initial.update(
            first_name=person.user.first_name,
            last_name=person.user.last_name,
            email=person.user.email,
        )
