import io
from pathlib import Path

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, reverse
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import DeleteView, FormView, UpdateView

from peoplefinder.forms.profile import ProfileForm, ProfileLeavingDitForm
from peoplefinder.forms.role import RoleForm
from peoplefinder.models import Person
from peoplefinder.services.audit_log import AuditLogService
from peoplefinder.services.image import ImageService
from peoplefinder.services.person import PersonService
from peoplefinder.services.team import TeamService

from .base import PeoplefinderView


class CannotDeleteOwnProfileError(Exception):
    pass


class ProfileLegacyView(PeoplefinderView):
    def get(self, request: HttpRequest, profile_legacy_slug: str) -> HttpResponse:
        profile = get_object_or_404(Person, legacy_slug=profile_legacy_slug)

        return redirect(reverse("profile-view", kwargs={"profile_slug": profile.slug}))


class ProfileDetailView(DetailView, PeoplefinderView):
    model = Person
    context_object_name = "profile"
    template_name = "peoplefinder/profile.html"
    slug_url_kwarg = "profile_slug"
    queryset = Person.objects.with_profile_completion()

    def get_context_data(self, **kwargs: dict) -> dict:
        context = super().get_context_data(**kwargs)

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

        return context


@method_decorator(transaction.atomic, name="post")
class ProfileEditView(SuccessMessageMixin, UpdateView, PeoplefinderView):
    model = Person
    context_object_name = "profile"
    form_class = ProfileForm
    template_name = "peoplefinder/profile-edit.html"
    slug_url_kwarg = "profile_slug"
    success_message = "Your profile has been updated"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        profile = context["profile"]
        roles = profile.roles.select_related("team").all()

        role_forms = [RoleForm(instance=role) for role in roles]

        context.update(roles=roles, role_forms=role_forms)

        return context

    def form_valid(self, form):
        # saves the form
        response = super().form_valid(form)

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

        with io.BytesIO() as photo_content:
            # save the cropped photo to the in-memory file object
            cropped_photo.save(photo_content, format=photo_ext)
            # tell django to save the cropped image
            profile.photo.save(photo_path.name, content=photo_content)

        # Let's also save a smaller version of the profile photo.
        resized_photo = ImageService.resize_image(cropped_photo, 150, 150)

        with io.BytesIO() as photo_content:
            resized_photo.save(photo_content, format=photo_ext)
            profile.photo_small.save(photo_path.name, content=photo_content)


class ProfileLeavingDitView(SuccessMessageMixin, FormView, PeoplefinderView):
    template_name = "peoplefinder/profile-leaving-dit.html"
    form_class = ProfileLeavingDitForm

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        self.profile = Person.objects.get(slug=self.kwargs["profile_slug"])

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
class ProfileDeleteView(DeleteView, PeoplefinderView):
    model = Person
    success_url = reverse_lazy("delete-confirmation")

    def get_object(self, queryset=None):
        return Person.objects.get(slug=self.kwargs["profile_slug"])

    def delete(self, request, *args, **kwargs):
        person = self.get_object()
        if request.user == person.user:
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


class ProfileConfirmDetailsView(UserPassesTestMixin, PeoplefinderView):
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)

        self.person = Person.objects.get(slug=self.kwargs["profile_slug"])

    def test_func(self):
        return self.request.user == self.person.user

    def post(self, request, profile_slug, *args, **kwargs):
        self.person.edited_or_confirmed_at = timezone.now()
        self.person.save()

        messages.success(request, "Your details have been successfully confirmed.")

        # Tell HTMX to refresh the page.
        return HttpResponse(headers={"HX-Refresh": "true"})
