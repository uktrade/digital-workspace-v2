from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import SuspiciousOperation
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

from peoplefinder.forms.role import RoleForm
from peoplefinder.models import Person, TeamMember
from peoplefinder.services.team import TeamService
from .base import PeoplefinderView


class RoleFormView(UserPassesTestMixin, PeoplefinderView):
    """A role form view which responds with an updated HTML form response."""

    def test_func(self) -> bool:
        # The profile must be that of the logged in user or an admin user.
        return self.profile.user == self.request.user or self.request.user.is_staff

    def dispatch(self, request, *args, **kwargs):
        self.profile_slug = kwargs["profile_slug"]
        self.profile = Person.objects.get(slug=self.profile_slug)

        self.role_pk = kwargs.get("role_pk")

        self.role = None

        if self.role_pk:
            self.role = TeamMember.objects.get(pk=self.role_pk)

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        context = {
            "profile": self.profile,
            "role": self.role,
            "form": RoleForm(initial={"person": self.profile}),
        }

        return render(
            request, "peoplefinder/components/role-edit.html", context=context
        )

    def post(self, request, *args, **kwargs):
        form = RoleForm(request.POST, instance=self.role)

        if form.is_valid():
            if form.cleaned_data["person"] != self.profile:
                raise SuspiciousOperation(
                    "Submitted person does not match profile from URL"
                )

            form.save()
            # a new role was saved
            if self.role is None:
                self.role = form.instance
                messages.success(request, "Role created successfully")
            else:
                messages.success(request, "Role updated successfully")
        else:
            messages.error(request, "Role not saved - please check form for errors")

        context = {
            "profile": self.profile,
            "role": self.role,
            "form": form,
        }

        return render(
            request, "peoplefinder/components/role-edit.html", context=context
        )

    def delete(self, request, *args, **kwargs):
        if self.role:
            self.role.delete()

        # the empty response is for htmx to remove the role from the DOM
        return HttpResponse("")


class TeamSelectView(PeoplefinderView):
    def get(self, request):
        team_select_data = list(TeamService().get_team_select_data())

        return JsonResponse(team_select_data, safe=False)
