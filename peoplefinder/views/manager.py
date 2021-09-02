from django.db.models import Value
from django.db.models.functions import Concat
from django.views.generic import TemplateView

from peoplefinder.models import Person
from .base import PeoplefinderView


class ManagerBaseView(TemplateView, PeoplefinderView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        profile = Person.objects.get(slug=kwargs["profile_slug"])
        context["profile"] = profile

        return context


class ManagerSelect(ManagerBaseView):
    template_name = "peoplefinder/components/manager/main.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        manager = Person.objects.get(slug=kwargs["manager_slug"])
        context["manager"] = manager

        return context


class ManagerUpdate(ManagerBaseView):
    template_name = "peoplefinder/components/manager/search-form.html"


class ManagerCancel(ManagerBaseView):
    template_name = "peoplefinder/components/manager/main.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["manager"] = context["profile"].manager

        return context


class ManagerSearch(ManagerBaseView):
    template_name = "peoplefinder/components/manager/search-results.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        name = self.request.GET["name"]

        people = None
        message = None

        if name:
            people = (
                Person.objects.annotate(
                    full_name_search=Concat(
                        "user__first_name", Value(" "), "user__last_name"
                    )
                )
                .filter(full_name_search__icontains=name)
                .exclude(pk=context["profile"])
            )

            if not people:
                message = f'No search results for name "{name}"'
        else:
            message = "Please enter a name"

        context.update(people=people, message=message)

        return context
