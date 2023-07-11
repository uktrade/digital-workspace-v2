from django import forms
from django.contrib.auth import get_user_model
from django.core.validators import ValidationError, validate_email

from peoplefinder.models import Person
from peoplefinder.services.person import PersonService


User = get_user_model()
email_choice_field = forms.ChoiceField(widget=forms.Select)


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
            "buildings",
            "regional_building",
            "international_building",
            "location_in_building",
            "workdays",
            "grade",
            "manager",
            "do_not_work_for_dit",
            "key_skills",
            "other_key_skills",
            "fluent_languages",
            "intermediate_languages",
            "learning_interests",
            "other_learning_interests",
            "networks",
            "professions",
            "additional_roles",
            "other_additional_roles",
            "previous_experience",
            "photo",
        ]
        widgets = {
            "email": email_choice_field,
            "workdays": forms.CheckboxSelectMultiple,
            "key_skills": forms.CheckboxSelectMultiple,
            "learning_interests": forms.CheckboxSelectMultiple,
            "networks": forms.CheckboxSelectMultiple,
            "professions": forms.CheckboxSelectMultiple,
            "additional_roles": forms.CheckboxSelectMultiple,
            "buildings": forms.CheckboxSelectMultiple,
        }

    # Override manager to avoid using IDs and enforce the use of UUIDs (slugs).
    manager = forms.UUIDField(required=False)
    # photo crop fields
    x = forms.IntegerField(required=False)
    y = forms.IntegerField(required=False)
    width = forms.IntegerField(required=False)
    height = forms.IntegerField(required=False)
    remove_photo = forms.BooleanField(required=False)

    # These fields are disabled by default as only a superuser can edit them. Disabled
    # fields cannot be tampered with and will fall back to their initial value.
    is_superuser = forms.BooleanField(
        disabled=True,
        required=False,
        label="Allow this person to administrate People Finder",
    )
    is_team_admin = forms.BooleanField(
        disabled=True, required=False, label="Allow this person to manage teams"
    )
    is_person_admin = forms.BooleanField(
        disabled=True, required=False, label="Allow this person to manage people"
    )

    def __init__(self, *args, **kwargs) -> None:
        self.request = kwargs.pop("request", None)

        super().__init__(*args, **kwargs)

        person = self.instance
        user = person.user

        self.fields["first_name"].widget.attrs.update(
            {"class": "govuk-input govuk-!-width-one-half"}
        )
        self.fields["last_name"].widget.attrs.update(
            {"class": "govuk-input govuk-!-width-one-half"}
        )
        self.fields["pronouns"].widget.attrs.update(
            {"class": "govuk-input govuk-!-width-one-half"}
        )
        self.fields["email"].widget.attrs.update(
            {"class": "govuk-select govuk-!-width-one-half"}
        )
        self.fields["email"].choices = self.get_email_choices()
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
        self.fields["buildings"].widget.attrs.update(
            {"class": "govuk-checkboxes__input"}
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
        self.fields["fluent_languages"].widget.attrs.update(
            {"class": "govuk-input govuk-!-width-one-half"}
        )
        self.fields["intermediate_languages"].widget.attrs.update(
            {"class": "govuk-input govuk-!-width-one-half"}
        )
        self.fields["learning_interests"].widget.attrs.update(
            {"class": "govuk-checkboxes__input"}
        )
        self.fields["other_learning_interests"].widget.attrs.update(
            {"class": "govuk-input govuk-!-width-one-half"}
        )
        self.fields["networks"].widget.attrs.update(
            {"class": "govuk-checkboxes__input"}
        )
        self.fields["professions"].widget.attrs.update(
            {"class": "govuk-checkboxes__input"}
        )
        self.fields["additional_roles"].widget.attrs.update(
            {"class": "govuk-checkboxes__input"}
        )
        self.fields["other_additional_roles"].widget.attrs.update(
            {"class": "govuk-input govuk-!-width-one-half"}
        )
        self.fields["previous_experience"].widget.attrs.update(
            {"class": "govuk-textarea", "rows": 5}
        )
        # Photo is a custom component
        self.fields["is_superuser"].widget.attrs.update(
            {"class": "govuk-checkboxes__input", "form": "edit-profile"}
        )
        self.fields["is_team_admin"].widget.attrs.update(
            {"class": "govuk-checkboxes__input", "form": "edit-profile"}
        )
        self.fields["is_person_admin"].widget.attrs.update(
            {"class": "govuk-checkboxes__input", "form": "edit-profile"}
        )

        self.initial.update(
            manager=person.manager and person.manager.slug,
            is_superuser=user and user.is_superuser,
            is_team_admin=user and user.groups.filter(name="Team Admin").exists(),
            is_person_admin=user and user.groups.filter(name="Person Admin").exists(),
        )

        # Enable the fields that only a superuser can edit.
        if self.request and self.request.user.is_superuser:
            self.fields["is_superuser"].disabled = False
            self.fields["is_team_admin"].disabled = False
            self.fields["is_person_admin"].disabled = False

    def clean_manager(self):
        manager_slug = self.cleaned_data["manager"]

        if not manager_slug:
            return None

        try:
            manager = Person.active.get(slug=manager_slug)
        except Person.DoesNotExist:
            raise ValidationError("Manager does not exist")

        return manager

    def clean_email(self):
        email = self.cleaned_data["email"]

        validate_email(email)

        verified_emails = PersonService.get_verified_emails(self.instance)
        if verified_emails == []:
            raise Exception("Could not retrieve valid emails for this user")
        if email not in verified_emails:
            raise ValidationError(
                "Email address must be officially assigned and verified by SSO authentication"
            )

        return email

    def clean(self):
        cleaned_data = super().clean()

        self.validate_photo(cleaned_data["photo"])

        return cleaned_data

    def get_email_choices(self):
        verified_emails = PersonService.get_verified_emails(self.instance)
        choices = []
        if self.instance.email in verified_emails:
            choices += [
                self.instance.email,
            ]
        choices += [email for email in verified_emails if email not in choices]
        if not choices:
            choices = [
                self.instance.email,
            ]
        return choices

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

    def save(self, commit=True):
        if "manager" in self.changed_data:
            self.instance.manager = self.cleaned_data["manager"]

        if self.cleaned_data["remove_photo"]:
            self.instance.photo = None
            self.instance.photo_small = None

        super().save(commit=commit)

        return self.instance


class ProfileLeavingDitForm(forms.Form):
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
