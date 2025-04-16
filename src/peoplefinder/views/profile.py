import io
from pathlib import Path
from typing import Any, Dict

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.forms.models import BaseModelForm
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseRedirect,
)
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.template.response import TemplateResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import decorator_from_middleware, method_decorator
from django.views.generic import TemplateView
from django.views.generic.detail import DetailView, SingleObjectMixin
from django.views.generic.edit import FormView, UpdateView
from django_hawk.middleware import HawkResponseMiddleware
from django_hawk.utils import DjangoHawkAuthenticationFailed, authenticate_request
from webpack_loader.utils import get_static

from peoplefinder.forms.crispy_helper import RoleFormsetFormHelper
from peoplefinder.forms.profile import ProfileLeavingDbtForm, ProfileUpdateUserForm
from peoplefinder.forms.profile_edit import (
    AccountSettingsForm,
    AdminProfileEditForm,
    ContactProfileEditForm,
    LocationProfileEditForm,
    PersonalProfileEditForm,
    SkillsProfileEditForm,
    TeamsProfileEditForm,
    TeamsProfileEditFormset,
)
from peoplefinder.forms.role import RoleFormsetForm
from peoplefinder.models import Person
from peoplefinder.services.audit_log import AuditLogService
from peoplefinder.services.image import ImageService
from peoplefinder.services.person import PersonService
from peoplefinder.services.team import TeamService
from peoplefinder.types import EditSections, ProfileSections

from .base import HtmxFormView, PeoplefinderView


User = get_user_model()


class CannotDeleteOwnProfileError(Exception):
    pass


class ProfileView(PeoplefinderView):
    def get_queryset(self):
        qs = super().get_queryset()

        if not self.request.user.has_perm("peoplefinder.can_view_inactive_profiles"):
            qs = qs.active()

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if profile := context.get("profile"):
            field_statuses = PersonService().profile_completion_field_statuses(profile)

            context.update(
                missing_profile_completion_fields=[
                    (
                        reverse(
                            "profile-edit-section",
                            kwargs={
                                "profile_slug": profile.slug,
                                "edit_section": PersonService().get_profile_completion_field_edit_section(
                                    field
                                ),
                            },
                        )
                        + "#"
                        + PersonService().get_profile_completion_field_form_id(field),
                        field.replace("_", " ").capitalize(),
                    )
                    for field, field_status in field_statuses.items()
                    if not field_status
                ],
            )
        return context


class ProfileLegacyView(ProfileView):
    def get(self, request: HttpRequest, profile_legacy_slug: str) -> HttpResponse:
        profile = get_object_or_404(Person, legacy_slug=profile_legacy_slug)

        return redirect(reverse("profile-view", kwargs={"profile_slug": profile.slug}))


class ProfileDetailView(ProfileView, DetailView):
    model = Person
    context_object_name = "profile"
    template_name = "peoplefinder/profile.html"
    slug_url_kwarg = "profile_slug"

    def get_context_data(self, **kwargs: dict) -> dict:
        context = super().get_context_data(**kwargs)

        context.update(
            profile_breadcrumbs=True,
        )

        profile = context["profile"]
        roles = profile.roles.select_related("team").all()

        context["roles"] = roles
        context["title"] = profile.full_name

        if roles:
            # TODO: How do we know which team to select as the main one?
            team = roles[0].team
            context["team"] = team
            # TODO: `parent_teams` is common to all views. Perhaps we should
            # refactor this into a common base view or mixin?
            context["parent_teams"] = list(TeamService().get_all_parent_teams(team)) + [
                team
            ]

        if self.request.user == profile.user or self.request.user.has_perm(
            "peoplefinder.view_auditlog"
        ):
            context["profile_audit_log"] = AuditLogService.get_audit_log(profile)
            context["profile_audit_log_excluded_keys"] = [
                "user_id",
                "manager_id",
                "created_at",
                "updated_at",
                "edited_or_confirmed_at",
            ]

        profile_section_dicts = []
        for profile_section in ProfileSections:
            profile_url = reverse("profile-view", kwargs={"profile_slug": profile.slug})
            profile_section_dicts.append(
                {
                    "profile_section": profile_section,
                    "title": profile_section.label,
                    "url": f"{profile_url}?profile_section={profile_section.value}",
                }
            )

        current_profile_section = ProfileSections(
            self.request.GET.get("profile_section", ProfileSections.TEAM_AND_ROLE)
        )

        current_tab = {
            "value": current_profile_section.value,
            "title": current_profile_section.label,
            "values": PersonService().get_profile_section_values(
                profile,
                current_profile_section,
            ),
            "empty_text": PersonService().get_profile_section_empty_text(
                current_profile_section,
            ),
        }

        context.update(
            current_tab=current_tab,
            profile_section_dicts=profile_section_dicts,
            show_confirm_my_details=(
                profile.is_active
                and profile.is_stale
                and self.request.user == profile.user
            ),
            show_activate_profile=(
                not profile.is_active
                and self.request.user.has_perm("peoplefinder.delete_person")
            ),
        )

        return context


def profile_edit_blank_teams_form(
    request: HttpRequest, *args, **kwargs
) -> HttpResponse:
    prefix = request.GET["prefix"] + "-" + request.GET["new_form_number"]
    profile_slug = kwargs["profile_slug"]
    person = Person.objects.get(slug=profile_slug)
    form = RoleFormsetForm(
        initial={"person": person},
        prefix=prefix,
    )
    return render(
        request,
        "peoplefinder/components/profile/edit/profile-edit-teams-blank-form.html",
        {"form": form},
    )


def redirect_to_profile_edit(request: HttpRequest, *args, **kwargs) -> HttpResponse:
    edit_section_kwargs = kwargs.copy()
    edit_section_kwargs["edit_section"] = "personal"
    return redirect(reverse("profile-edit-section", kwargs=edit_section_kwargs))


@method_decorator(transaction.atomic, name="post")
class ProfileEditView(SuccessMessageMixin, ProfileView, UpdateView):
    model = Person
    context_object_name = "profile"
    template_name = "peoplefinder/profile-edit.html"
    slug_url_kwarg = "profile_slug"
    success_message = "Your profile has been updated"

    form_classes = {
        EditSections.PERSONAL: PersonalProfileEditForm,
        EditSections.CONTACT: ContactProfileEditForm,
        EditSections.TEAMS: TeamsProfileEditForm,
        EditSections.LOCATION: LocationProfileEditForm,
        EditSections.SKILLS: SkillsProfileEditForm,
        EditSections.ACCOUNT_SETTINGS: AccountSettingsForm,
        EditSections.ADMIN: AdminProfileEditForm,
    }

    def get_form_class(self) -> type[BaseModelForm]:
        return self.form_classes[self.edit_section]

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.edit_section = EditSections(
            kwargs.get(
                "edit_section",
                EditSections.PERSONAL.value,
            )
        )

        if self.edit_section == EditSections.ADMIN and not request.user.is_superuser:
            return HttpResponseForbidden()

        self.teams_formset = None
        if self.edit_section == EditSections.TEAMS:
            self.teams_formset = self.get_teams_formset(self.request)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            "profile-edit-section",
            kwargs={
                "profile_slug": self.object.slug,
                "edit_section": self.edit_section.value,
            },
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"request_user": self.request.user})

        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        profile = context["profile"]
        roles = profile.roles.select_related("team").all()
        team = None
        if roles:
            team = roles[0].team

        update_user_form = ProfileUpdateUserForm(
            initial={"username": profile.user and profile.user.username},
            profile=profile,
        )

        edit_sections = [section for section in EditSections]
        if not self.request.user.is_superuser:
            edit_sections.remove(EditSections.ADMIN)

        page_title = f"Edit profile: {self.edit_section.label.lower()}"
        if self.edit_section == EditSections.ACCOUNT_SETTINGS:
            page_title = EditSections.ACCOUNT_SETTINGS.label

        context.update(
            profile_breadcrumbs=True,
            extra_breadcrumbs=[(None, "Edit profile")],
            page_title=page_title,
            current_edit_section=self.edit_section,
            edit_sections=edit_sections,
            profile_slug=profile.slug,
            roles=roles,
            team=team,
            update_user_form=update_user_form,
        )

        if self.edit_section == EditSections.TEAMS:
            context.update(
                teams_formset=self.teams_formset,
                teams_formset_helper=RoleFormsetFormHelper(),
                teams_formset_blank_form_url=reverse(
                    "profile-edit-blank-teams-form",
                    kwargs={"profile_slug": self.object.slug},
                )
                + "?prefix="
                + self.teams_formset.prefix,
            )

        edit_menu_items = [
            {
                "title": section.label,
                "url": reverse(
                    "profile-edit-section",
                    kwargs={
                        "profile_slug": profile.slug,
                        "edit_section": section.value,
                    },
                ),
                "active": section == self.edit_section,
            }
            for section in edit_sections
        ]

        context.update(
            edit_menu_items=edit_menu_items,
        )

        return context

    def get_teams_formset(self, request: HttpRequest) -> TeamsProfileEditFormset:
        self.object = self.get_object()
        teams_formset_kwargs = {
            "prefix": "teams",
            "initial": [
                {
                    "person": self.object,
                    "team": None,
                    "job_title": None,
                    "head_of_team": False,
                }
            ],
            "queryset": self.object.roles.all(),
        }
        if request.method == "POST":
            teams_formset = TeamsProfileEditFormset(
                request.POST,
                request.FILES,
                **teams_formset_kwargs,
            )
        else:
            teams_formset = TeamsProfileEditFormset(
                **teams_formset_kwargs,
            )

        return teams_formset

    def form_invalid(self, form):
        """If the form is invalid, render the invalid form."""
        return self.render_to_response(
            self.get_context_data(
                form=form,
                teams_formset=self.teams_formset,
            )
        )

    def form_valid(self, form):
        # Check if the teams formset is valid
        if self.edit_section == EditSections.TEAMS:
            if not self.teams_formset.is_valid():
                return self.form_invalid(form)

        # Saves the form
        response = super().form_valid(form)

        # Saves the teams formset
        if self.teams_formset:
            self.teams_formset.save()

        if isinstance(form, AdminProfileEditForm):
            PersonService.update_groups_and_permissions(
                person=self.object,
                is_person_admin=form.cleaned_data["is_person_admin"],
                is_team_admin=form.cleaned_data["is_team_admin"],
                is_superuser=form.cleaned_data["is_superuser"],
            )

        if "photo" in form.changed_data:
            self.crop_photo(form)

        if form.has_changed():
            PersonService().profile_updated(
                self.request, self.object, self.request.user
            )

        return response

    def crop_photo(self, form):
        profile = self.object
        photo_path = Path(profile.photo.name)

        photo = form.cleaned_data["photo"]

        photo_ext = photo_path.suffix
        # strip leading period
        photo_ext = photo_ext.lstrip(".")

        # Pillow doesn't like JPG as a file extension ¯\_(ツ)_/¯
        if photo_ext.upper() == "JPG":
            photo_ext = "JPEG"

        cropped_photo = ImageService.crop_image(
            photo,
            form.cleaned_data["x"],
            form.cleaned_data["y"],
            form.cleaned_data["width"],
            form.cleaned_data["height"],
        )
        resized_photo = ImageService.resize_image(cropped_photo, 512, 512)

        with io.BytesIO() as photo_content:
            # save the cropped photo to the in-memory file object
            resized_photo.save(photo_content, format=photo_ext)
            # tell django to save the cropped image
            profile.photo.save(photo_path.name, content=photo_content)

        # Let's also save a smaller version of the profile photo.
        resized_photo_small = ImageService.resize_image(resized_photo, 150, 150)

        with io.BytesIO() as photo_content:
            resized_photo_small.save(photo_content, format=photo_ext)
            profile.photo_small.save(photo_path.name, content=photo_content)

    def get_field_locations(self):
        field_locations: Dict[str, EditSections] = {}

        for edit_section, form_class in self.form_classes.items():
            for field_name in form_class.base_fields.keys():
                field_locations[field_name] = edit_section

        return field_locations


class ProfileLeavingDbtView(SuccessMessageMixin, ProfileView, FormView):
    template_name = "peoplefinder/profile-leaving-dit.html"
    form_class = ProfileLeavingDbtForm

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        self.profile = Person.active.get(slug=self.kwargs["profile_slug"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["profile"] = self.profile

        return context

    def form_valid(self, form):
        person_service = PersonService()

        person_service.left_dit(
            request=self.request,
            person=self.profile,
            reported_by=self.request.user.profile,
            comment=form.cleaned_data.get("comment"),
        )

        return super().form_valid(form)

    def get_success_url(self):
        return reverse("profile-view", kwargs={"profile_slug": self.profile.slug})

    def get_success_message(self, cleaned_data):
        return f"A deletion request for {self.profile} has been sent to support"


@method_decorator(transaction.atomic, name="post")
class ProfileDeleteView(SingleObjectMixin, ProfileView):
    model = Person
    slug_url_kwarg = "profile_slug"
    success_url = reverse_lazy("delete-confirmation")

    def post(self, request, *args, **kwargs):
        person = self.get_object()

        if person.user and request.user.pk == person.user.pk:
            raise CannotDeleteOwnProfileError()

        self.request.session["profile_name"] = person.full_name

        PersonService().profile_deleted(self.request, person, self.request.user)

        return HttpResponseRedirect(self.success_url)


class DeleteConfirmationView(TemplateView):
    template_name = "peoplefinder/delete-confirmation.html"

    def dispatch(self, request, *args, **kwargs):
        profile_name = self.request.session.get("profile_name", None)

        if not profile_name:
            return redirect("people-home")

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["profile_name"] = self.request.session.get("profile_name", None)

        del self.request.session["profile_name"]

        return context


class ProfileHtmxActionView(PeoplefinderView):
    success_message = ""

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        self.person = Person.objects.get(slug=self.kwargs["profile_slug"])

    def post(self, request, profile_slug, *args, **kwargs):
        self.action()

        if self.success_message:
            messages.success(request, self.success_message)

        # Tell HTMX to refresh the page.
        return HttpResponse(headers={"HX-Refresh": "true"})

    def action(self):
        raise NotImplementedError


class ProfileConfirmDetailsView(UserPassesTestMixin, ProfileHtmxActionView):
    success_message = "Your details have been successfully confirmed."

    def test_func(self):
        return self.request.user == self.person.user

    def action(self):
        self.person.edited_or_confirmed_at = timezone.now()
        self.person.save()


class ProfileActivateAction(
    UserPassesTestMixin, PermissionRequiredMixin, ProfileHtmxActionView
):
    success_message = "This profile has been activated."
    permission_required = "peoplefinder.delete_person"
    permission_denied_message = "You do not have permission to activate this profile."

    def test_func(self):
        return self.request.user != self.person.user

    def action(self):
        self.person.is_active = True
        self.person.became_inactive = None
        self.person.save()


class ProfileUpdateUserView(UserPassesTestMixin, SuccessMessageMixin, HtmxFormView):
    template_name = "peoplefinder/components/update-user-form.html"
    form_class = ProfileUpdateUserForm
    success_message = "User has been updated"

    def test_func(self):
        return self.request.user.is_superuser

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        self.person = Person.objects.get(slug=self.kwargs["profile_slug"])

    def get_context_data(self, **kwargs):
        context = {"profile": self.person}

        return super().get_context_data(**kwargs) | context

    def get_form_kwargs(self):
        return super().get_form_kwargs() | {"profile": self.person}

    def get_initial(self):
        return {"username": self.person.user and self.person.user.username}

    def form_valid(self, form):
        user = User.objects.get(username=form.cleaned_data["username"])

        if hasattr(user, "profile"):
            old_profile = user.profile
            old_profile.user = None
            old_profile.save()

        self.person.user = user
        self.person.save()

        return super().form_valid(form)


def get_profile_by_staff_sso_id(request, staff_sso_id):
    person = get_object_or_404(Person, user__legacy_sso_user_id=staff_sso_id)

    return redirect(person)


@decorator_from_middleware(HawkResponseMiddleware)
def get_profile_card(request, staff_sso_email_user_id):
    try:
        authenticate_request(request=request)
    except DjangoHawkAuthenticationFailed:
        return HttpResponse(status=401)

    try:
        person = Person.objects.filter(user__username=staff_sso_email_user_id).get()
    except (Person.DoesNotExist, Person.MultipleObjectsReturned):
        person = None

    return TemplateResponse(
        request,
        "peoplefinder/components/profile-card.html",
        {
            "profile": person,
            "profile_url": request.build_absolute_uri(person.get_absolute_url()),
            "no_photo_url": request.build_absolute_uri(get_static("no-photo.png")),
        },
    )
