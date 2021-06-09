from django import forms
from django.core.validators import ValidationError

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
            "workdays",
            "grade",
            "manager",
            "do_not_work_for_dit",
            "key_skills",
            "other_key_skills",
            "photo",
        ]
        widgets = {
            "workdays": forms.CheckboxSelectMultiple,
            "key_skills": forms.CheckboxSelectMultiple,
        }

    first_name = forms.CharField()
    last_name = forms.CharField()
    email = forms.EmailField(
        label="Main work email address",
        help_text=(
            "Enter your own official work email address provided by the"
            " organisation you are directly employed by or contracted to."
        ),
    )
    # photo crop fields
    x = forms.IntegerField(required=False)
    y = forms.IntegerField(required=False)
    width = forms.IntegerField(required=False)
    height = forms.IntegerField(required=False)

    def __init__(self, *args, **kwargs) -> None:
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
        self.fields["workdays"].widget.attrs.update(
            {"class": "govuk-checkboxes__input"}
        )
        self.fields["grade"].widget.attrs.update(
            {"class": "govuk-select govuk-!-width-one-half"}
        )
        # Manager is a custom component
        self.fields["do_not_work_for_dit"].widget.attrs.update(
            {"class": "govuk-checkboxes__input"}
        )
        self.fields["key_skills"].widget.attrs.update(
            {"class": "govuk-checkboxes__input"}
        )
        self.fields["other_key_skills"].widget.attrs.update(
            {"class": "govuk-input govuk-!-width-one-half"}
        )
        # Photo is a custom component

        self.initial.update(
            first_name=person.user.first_name,
            last_name=person.user.last_name,
            email=person.user.email,
        )

    def clean(self):
        cleaned_data = super().clean()

        self.validate_photo(cleaned_data["photo"])

    def validate_photo(self, photo):
        if not hasattr(photo, "image"):
            return

        if photo.image.width < 500:
            self.add_error("photo", ValidationError("Width is less than 500px"))

        if photo.image.height < 500:
            self.add_error("photo", ValidationError("Height is less than 500px"))

        # 8mb in bytes
        if photo.size > 1024 * 1024 * 8:
            self.add_error("photo", ValidationError("File size is greater than 8MB"))
