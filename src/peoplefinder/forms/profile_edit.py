from typing import List

from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import HTML, Field, Fieldset, Layout, Size
from django import forms
from django.core.validators import ValidationError, validate_email
from django.template import Context, Template

from peoplefinder.forms.crispy_layout import GovUKDetails
from peoplefinder.forms.profile import GovUkRadioSelect, GroupedModelChoiceField
from peoplefinder.forms.role import RoleForm
from peoplefinder.models import Person, TeamMember, UkStaffLocation
from peoplefinder.services.person import PersonService


class PersonalProfileEditForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = [
            "first_name",
            "preferred_first_name",
            "last_name",
            "pronouns",
            "photo",
            "name_pronunciation",
        ]

    # # photo crop fields
    x = forms.IntegerField(required=False)
    y = forms.IntegerField(required=False)
    width = forms.IntegerField(required=False)
    height = forms.IntegerField(required=False)
    remove_photo = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop("request_user", None)
        super().__init__(*args, **kwargs)

        first_name_label = self.fields["first_name"].label
        self.fields["first_name"].label = ""
        self.fields["first_name"].disabled = True

        preferred_first_name_label = (
            self.fields["preferred_first_name"].label + " (optional)"
        )
        self.fields["preferred_first_name"].label = ""

        last_name_label = self.fields["last_name"].label
        self.fields["last_name"].label = ""

        pronouns_label = self.fields["pronouns"].label + " (optional)"
        self.fields["pronouns"].label = ""

        name_pronunciation_label = (
            self.fields["name_pronunciation"].label + " (optional)"
        )
        self.fields["name_pronunciation"].label = ""

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                "first_name",
                legend_size=Size.MEDIUM,
                legend=first_name_label,
            ),
            Fieldset(
                "preferred_first_name",
                legend_size=Size.MEDIUM,
                legend=preferred_first_name_label,
            ),
            Fieldset(
                "last_name",
                legend_size=Size.MEDIUM,
                legend=last_name_label,
            ),
            Fieldset(
                "pronouns",
                legend_size=Size.MEDIUM,
                legend=pronouns_label,
            ),
            Fieldset(
                "name_pronunciation",
                legend_size=Size.MEDIUM,
                legend=name_pronunciation_label,
            ),
            Fieldset(
                HTML(
                    """
                    {% load static %}
                    {% load webpack_static from webpack_loader %}

                    <script src="{% static 'peoplefinder/profile-photo.js' %}"></script>
                    <profile-photo
                        name="photo"
                        photo-url="{% if profile.photo %}{{ profile.photo.url }}{% endif %}"
                        no-photo-url="{% webpack_static 'no-photo-large.png' %}"
                        x-name="x"
                        y-name="y"
                        width-name="width"
                        height-name="height"
                        remove-photo-name="remove_photo">
                    </profile-photo>
                    """
                ),
                legend_size=Size.MEDIUM,
                legend="Photo",
                css_class="govuk-!-margin-bottom-0",
            ),
        )

    def clean(self):
        cleaned_data = super().clean()

        self.validate_photo(cleaned_data["photo"])

        return cleaned_data

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
        if self.cleaned_data["remove_photo"]:
            self.instance.photo = None
            self.instance.photo_small = None

        return super().save(commit=commit)


class ContactProfileEditForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = [
            "contact_email",
            "primary_phone_number",
            "secondary_phone_number",
        ]

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop("request_user", None)
        super().__init__(*args, **kwargs)

        contact_email_label = self.fields["contact_email"].label
        self.fields["contact_email"].required = True
        self.fields["contact_email"].label = ""

        primary_phone_number_label = self.fields["primary_phone_number"].label
        self.fields["primary_phone_number"].label = ""

        secondary_phone_number_label = (
            self.fields["secondary_phone_number"].label + " (optional)"
        )
        self.fields["secondary_phone_number"].label = ""

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                "contact_email",
                legend_size=Size.MEDIUM,
                legend=contact_email_label,
            ),
            Fieldset(
                "primary_phone_number",
                legend_size=Size.MEDIUM,
                legend=primary_phone_number_label,
            ),
            Fieldset(
                "secondary_phone_number",
                legend_size=Size.MEDIUM,
                legend=secondary_phone_number_label,
                css_class="govuk-!-margin-bottom-0",
            ),
        )


class TeamsProfileEditForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = [
            "grade",
            "manager",
            "do_not_work_for_dit",
        ]

    # Override manager to avoid using IDs and enforce the use of UUIDs (slugs).
    manager = forms.UUIDField(
        label="Who is your line manager?",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop("request_user", None)
        super().__init__(*args, **kwargs)

        person = self.instance

        self.initial.update(
            manager=person.manager and person.manager.slug,
        )

        grade_label = self.fields["grade"].label
        self.fields["grade"].label = ""

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                "grade",
                legend_size=Size.MEDIUM,
                legend=grade_label,
            ),
            Fieldset(
                HTML(
                    Template(
                        "{% include 'peoplefinder/components/manager/main.html' %}"
                    ).render(
                        Context({"profile": person, "manager": person.manager}),
                    )
                ),
                Field("do_not_work_for_dit"),
                legend_size=Size.MEDIUM,
                legend="Who is your line manager?",
                css_class="govuk-!-margin-bottom-0",
            ),
        )

    def clean_manager(self):
        manager_slug = self.cleaned_data["manager"]

        if not manager_slug:
            return None

        try:
            manager = Person.active.get(slug=manager_slug)
        except Person.DoesNotExist:
            raise ValidationError("Manager does not exist")

        return manager

    def save(self, commit=True):
        if "manager" in self.changed_data:
            self.instance.manager = self.cleaned_data["manager"]
        return super().save(commit=commit)


TeamsProfileEditFormset = forms.modelformset_factory(
    TeamMember,
    form=RoleForm,
    extra=0,
    can_delete=True,
)


class LocationProfileEditForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = [
            "uk_office_location",
            "remote_working",
            "usual_office_days",
            "location_in_building",
            "international_building",
            "workdays",
        ]
        widgets = {
            "remote_working": GovUkRadioSelect,
            "workdays": forms.CheckboxSelectMultiple,
        }

    uk_office_location = GroupedModelChoiceField(
        queryset=UkStaffLocation.objects.all()
        .filter(
            organisation__in=[
                "Department for Business and Trade",
            ]
        )
        .order_by(
            "city",
            "name",
        ),
        label="What is your office location?",
        help_text="Your base location as per your contract",
        group_field="city",
        empty_label="Select your office location",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop("request_user", None)
        super().__init__(*args, **kwargs)

        remote_working_choices = list(self.fields["remote_working"].choices)
        if remote_working_choices[0][0] == "":
            remote_working_choices.pop(0)
        self.fields["remote_working"].choices = remote_working_choices

        usual_office_days_label = self.fields["usual_office_days"].label + " (optional)"
        self.fields["usual_office_days"].label = ""

        uk_office_location_label = self.fields["uk_office_location"].label
        self.fields["uk_office_location"].label = ""

        remote_working_label = self.fields["remote_working"].label
        self.fields["remote_working"].label = ""

        location_in_building_label = (
            self.fields["location_in_building"].label + " (optional)"
        )
        self.fields["location_in_building"].label = ""

        international_building_label = (
            self.fields["international_building"].label + " (optional)"
        )
        self.fields["international_building"].label = ""

        workdays_label = self.fields["workdays"].label + " (optional)"
        self.fields["workdays"].label = ""

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                "uk_office_location",
                legend_size=Size.MEDIUM,
                legend=uk_office_location_label,
            ),
            Fieldset(
                "remote_working",
                legend_size=Size.MEDIUM,
                legend=remote_working_label,
            ),
            Fieldset(
                "usual_office_days",
                legend_size=Size.MEDIUM,
                legend=usual_office_days_label,
            ),
            Fieldset(
                "location_in_building",
                legend_size=Size.MEDIUM,
                legend=location_in_building_label,
            ),
            Fieldset(
                "international_building",
                legend_size=Size.MEDIUM,
                legend=international_building_label,
            ),
            Fieldset(
                "workdays",
                legend_size=Size.MEDIUM,
                legend=workdays_label,
                css_class="govuk-!-margin-bottom-0",
            ),
        )


class SkillsProfileEditForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = [
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
        ]
        widgets = {
            "key_skills": forms.CheckboxSelectMultiple,
            "learning_interests": forms.CheckboxSelectMultiple,
            "networks": forms.CheckboxSelectMultiple,
            "professions": forms.CheckboxSelectMultiple,
            "additional_roles": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop("request_user", None)
        super().__init__(*args, **kwargs)

        key_skills_label = self.fields["key_skills"].label
        self.fields["key_skills"].label = ""

        other_key_skills_label = self.fields["other_key_skills"].label
        self.fields["other_key_skills"].label = ""

        fluent_languages_label = self.fields["fluent_languages"].label
        self.fields["fluent_languages"].label = ""

        intermediate_languages_label = self.fields["intermediate_languages"].label
        self.fields["intermediate_languages"].label = ""

        learning_interests_label = self.fields["learning_interests"].label
        self.fields["learning_interests"].label = ""

        other_learning_interests_label = self.fields["other_learning_interests"].label
        self.fields["other_learning_interests"].label = ""

        networks_label = self.fields["networks"].label
        self.fields["networks"].label = ""

        professions_label = self.fields["professions"].label
        self.fields["professions"].label = ""

        additional_roles_label = self.fields["additional_roles"].label
        self.fields["additional_roles"].label = ""

        other_additional_roles_label = self.fields["other_additional_roles"].label
        self.fields["other_additional_roles"].label = ""

        previous_experience_label = self.fields["previous_experience"].label
        self.fields["previous_experience"].label = ""

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                GovUKDetails(
                    Fieldset(
                        "key_skills",
                        legend_size=Size.SMALL,
                        legend=key_skills_label,
                    ),
                    Fieldset(
                        "other_key_skills",
                        legend_size=Size.SMALL,
                        legend=other_key_skills_label,
                    ),
                    summary="Add skills",
                ),
                GovUKDetails(
                    Fieldset(
                        "fluent_languages",
                        legend_size=Size.SMALL,
                        legend=fluent_languages_label,
                    ),
                    Fieldset(
                        "intermediate_languages",
                        legend_size=Size.SMALL,
                        legend=intermediate_languages_label,
                    ),
                    summary="Add languages",
                ),
                GovUKDetails(
                    Fieldset(
                        "learning_interests",
                        legend_size=Size.SMALL,
                        legend=learning_interests_label,
                    ),
                    Fieldset(
                        "other_learning_interests",
                        legend_size=Size.SMALL,
                        legend=other_learning_interests_label,
                    ),
                    summary="Add learning and development interests",
                ),
                GovUKDetails(
                    Fieldset(
                        "networks",
                        legend_size=Size.SMALL,
                        legend=networks_label,
                    ),
                    summary="Add networks I belong to",
                ),
                GovUKDetails(
                    Fieldset(
                        "professions",
                        legend_size=Size.SMALL,
                        legend=professions_label,
                    ),
                    summary="Add professions I belong to",
                ),
                GovUKDetails(
                    Fieldset(
                        "additional_roles",
                        legend_size=Size.SMALL,
                        legend=additional_roles_label,
                    ),
                    Fieldset(
                        "other_additional_roles",
                        legend_size=Size.SMALL,
                        legend=other_additional_roles_label,
                    ),
                    summary="Add additional roles and responsibilities",
                ),
                GovUKDetails(
                    Fieldset(
                        "previous_experience",
                        legend_size=Size.SMALL,
                        legend=previous_experience_label,
                    ),
                    summary="Add previous experience",
                ),
                legend_size=Size.MEDIUM,
                legend="Skills, interests and networks (optional)",
                css_class="govuk-!-margin-bottom-0",
            )
        )


class AccountSettingsForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = [
            "email",
        ]
        widgets = {
            "email": forms.Select,
        }

    email = forms.ChoiceField(
        label=Person._meta.get_field("email").verbose_name,
        help_text=Person._meta.get_field("email").help_text,
        required=True,
    )

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop("request_user", None)
        super().__init__(*args, **kwargs)

        email_label = self.fields["email"].label
        self.fields["email"].label = ""
        self.fields["email"].choices = [(e, e) for e in self.get_email_choices()]

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                Field.select("email"),
                legend_size=Size.MEDIUM,
                legend=email_label,
                css_class="govuk-!-margin-bottom-0",
            ),
        )

    def get_email_choices(self) -> List[str]:
        verified_emails = PersonService.get_verified_emails(self.instance)
        choices = []
        if self.instance.email in verified_emails:
            choices += [self.instance.email]
        choices += [email for email in verified_emails if email not in choices]
        if not choices:
            return [self.instance.email]
        return choices

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


class AdminProfileEditForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = [
            "is_superuser",
            "is_team_admin",
            "is_person_admin",
        ]

    # These fields are disabled by default as only a superuser can edit them. Disabled
    # fields cannot be tampered with and will fall back to their initial value.
    is_superuser = forms.BooleanField(
        disabled=True,
        required=False,
        label="Allow this person to administer People Finder",
    )
    is_team_admin = forms.BooleanField(
        disabled=True, required=False, label="Allow this person to manage teams"
    )
    is_person_admin = forms.BooleanField(
        disabled=True, required=False, label="Allow this person to manage people"
    )

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop("request_user", None)
        super().__init__(*args, **kwargs)

        person = self.instance
        user = person.user

        self.initial.update(
            is_superuser=user and user.is_superuser,
            is_team_admin=user and user.groups.filter(name="Team Admin").exists(),
            is_person_admin=user and user.groups.filter(name="Person Admin").exists(),
        )

        # Enable the fields that only a superuser can edit.
        if self.request_user and self.request_user.is_superuser:
            self.fields["is_superuser"].disabled = False
            self.fields["is_team_admin"].disabled = False
            self.fields["is_person_admin"].disabled = False

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field("is_superuser"),
            Field("is_team_admin"),
            Field("is_person_admin"),
        )
