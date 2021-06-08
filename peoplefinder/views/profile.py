import io
import os

from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView

from peoplefinder.forms.profile import ProfileForm
from peoplefinder.forms.role import RoleForm
from peoplefinder.models import Person
from peoplefinder.services.image import ImageService
from peoplefinder.services.team import TeamService
from .base import PeoplefinderView


class ProfileDetailView(DetailView, PeoplefinderView):
    model = Person
    context_object_name = "profile"
    template_name = "peoplefinder/profile.html"
    pk_url_kwarg = "profile_pk"

    def get_context_data(self, **kwargs: dict) -> dict:
        context = super().get_context_data(**kwargs)

        profile = context["profile"]
        roles = profile.roles.select_related("team").all()

        context["roles"] = roles
        context["title"] = profile.user.get_full_name()

        if roles:
            # TODO: How do we know which team to select as the main one?
            team = roles[0].team
            context["team"] = team
            # TODO: `parent_teams` is common to all views. Perhaps we should
            # refactor this into a common base view or mixin?
            context["parent_teams"] = list(TeamService().get_all_parent_teams(team)) + [
                team
            ]

        return context


class ProfileEditView(UserPassesTestMixin, UpdateView, PeoplefinderView):
    model = Person
    context_object_name = "profile"
    form_class = ProfileForm
    template_name = "peoplefinder/profile-edit.html"
    pk_url_kwarg = "profile_pk"

    def test_func(self) -> bool:
        # The profile must be that of the logged in user.
        return self.get_object().user == self.request.user

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

        if "photo" in form.changed_data:
            self.crop_photo(form)

        return response

    def crop_photo(self, form):
        profile = self.object
        photo = form.cleaned_data["photo"]

        photo_name = profile.photo.name
        _, photo_ext = os.path.splitext(profile.photo.name)
        # strip leading period
        photo_ext = photo_ext.lstrip(".")

        # Pillow doesn't like JPG as a file extension ¯\_(ツ)_/¯
        if photo_ext.upper() == "JPG":
            photo_ext = "JPEG"

        cropped_photo = ImageService().crop_image(
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
            profile.photo.save(photo_name, content=photo_content)
