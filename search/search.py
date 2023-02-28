from content.models import ContentPage
from tools.models import Tool
from news.models import NewsPage
from working_at_dit.models import PoliciesAndGuidanceHome
from peoplefinder.models import Person, Team


class SearchVector:
    def __init__(self, request):
        self.request = request

    def get_queryset(self):
        raise NotImplementedError

    def search(self, query, *args, **kwargs):
        queryset = self.get_queryset()
        results = queryset.search(query, *args, operator="and", **kwargs)

        return results


class PagesSearchVector(SearchVector):
    page_model = None

    def get_queryset(self):
        return self.page_model.objects.public().live()


class GuidanceSearchVector(PagesSearchVector):
    page_model = ContentPage

    def get_queryset(self):
        policies_and_guidance_home = PoliciesAndGuidanceHome.objects.first()

        return super().get_queryset().descendant_of(policies_and_guidance_home)


class NewsSearchVector(PagesSearchVector):
    page_model = NewsPage


class ToolsSearchVector(PagesSearchVector):
    page_model = Tool


class PeopleSearchVector(SearchVector):
    def get_queryset(self):
        people = Person.objects.all()

        if not self.request.user.has_perm("peoplefinder.delete_person"):
            people.active()

        people.prefetch_related("key_skills", "additional_roles", "teams")

        return people


class TeamsSearchVector(SearchVector):
    def get_queryset(self):
        return Team.objects.all().with_all_parents()
