# Integration / functional output tests
import pytest
from django.conf import settings
from django.core.management import call_command
from django.test import TestCase

from wagtail.search.backends import get_search_backend
from wagtail.search.index import AutocompleteField, SearchField

from content.models import ContentPage
from extended_search.query import Filtered
from extended_search.index import DWIndexedField as IndexedField
from extended_search.query_builder import CustomQueryBuilder
from extended_search.models import Setting
from extended_search.settings import SearchSettings, extended_search_settings
from news.factories import NewsPageFactory
from peoplefinder.services.person import PersonService
from peoplefinder.test.factories import PersonFactory, TeamFactory
from tools.tests.factories import ToolFactory
from user.models import User
from user.test.factories import UserFactory
from working_at_dit.models import PoliciesAndGuidanceHome
from working_at_dit.tests.factories import GuidanceFactory, HowDoIFactory, PolicyFactory


class TestGeneratedQuery:
    def find_filter(self, query):
        if isinstance(query, Filtered):
            self.filter_parts.append(query)
            return query
        if hasattr(query, "subqueries"):
            subs = []
            for q in query.subqueries:
                subs.append(self.find_filter(q))
            return subs
        return query.subquery

    @pytest.mark.django_db
    def test_generated_search_applies_baseclass_and_subclass_filters(self):
        query = CustomQueryBuilder.get_search_query(ContentPage, "foo")

        extended_models = (
            CustomQueryBuilder.get_extended_models_with_unique_indexed_fields(
                ContentPage
            )
        )

        self.filter_parts = []
        self.find_filter(query)

        num_excludes = 0
        assert len(self.filter_parts) == len(extended_models) + 1
        for r in self.filter_parts:
            field, lookup, value = r.filters[0]
            assert field == "content_type"
            assert lookup in ("contains", "excludes")
            if lookup == "excludes":
                num_excludes += 1
                assert (
                    f"{ContentPage._meta.app_label}.{ContentPage.__name__}" not in value
                )
                for model in extended_models:
                    assert f"{model._meta.app_label}.{model.__name__}" in value
            else:
                assert value in [
                    f"{model._meta.app_label}.{model.__name__}"
                    for model in extended_models
                ]
        assert num_excludes == 1


class TestExpectedSearchResults(TestCase):
    def setUp(self):
        """
        Create the following data for search testing:
        - 1 guidance page with "fruit" in the title
        - 1 policy page with "fruit" in the title
        - 1 howdoi page with "fruit" in the title
        - 1 tool page with "fruit" in the title
        - 1 news page with "fruit" in the title
        - 1 person with "fruit" in their name
        - 1 team with "fruit" in the name
        - 1 of each of the above without any "fruit" content
        """

        policies_and_guidance_home = PoliciesAndGuidanceHome.objects.first()
        self.content_owner = User.objects.get(username="johnsmith")
        self.content_owner_pages = [
            GuidanceFactory.create(
                parent=policies_and_guidance_home,
                title="How to eat Fruit",
                content_owner=self.content_owner.profile,
                content_contact_email=self.content_owner.email,
            ),
            GuidanceFactory.create(
                parent=policies_and_guidance_home,
                title="An irrelevant page",
                content_owner=self.content_owner.profile,
                content_contact_email=self.content_owner.email,
            ),
            PolicyFactory.create(
                parent=policies_and_guidance_home,
                title="What fruit can I eat?",
                content_owner=self.content_owner.profile,
                content_contact_email=self.content_owner.email,
            ),
            PolicyFactory.create(
                parent=policies_and_guidance_home,
                title="Policies not relating to food",
                content_owner=self.content_owner.profile,
                content_contact_email=self.content_owner.email,
            ),
            HowDoIFactory.create(
                title="How do I find fruit?",
                content_owner=self.content_owner.profile,
                content_contact_email=self.content_owner.email,
            ),
            HowDoIFactory.create(
                title="How to write test content",
                content_owner=self.content_owner.profile,
                content_contact_email=self.content_owner.email,
            ),
        ]
        self.pages = [
            ToolFactory.create(
                title="Fruit finder",
            ),
            ToolFactory.create(
                title="Internal tooling tool",
            ),
            NewsPageFactory.create(
                title="Big fruit news",
            ),
            NewsPageFactory.create(
                title="New news",
            ),
        ]
        self.people = [
            PersonFactory.create(
                first_name="Martin",
                last_name="Fruit",
                email="martin.fruit@example.com",
            ),
            PersonFactory.create(
                first_name="Adam", last_name="Ant", email="adam.ant@example.com"
            ),
        ]
        self.teams = [
            TeamFactory.create(
                name="Fruit pickers", slug="fruit-pickers", abbreviation="FRUIT"
            ),
            TeamFactory.create(name="Middle managers", slug="managers"),
        ]

        call_command("update_index")

        self.user = UserFactory()
        PersonService().create_user_profile(self.user)
        self.client.force_login(self.user)

    def test_workspace(self):
        response = self.client.get("/search/", {"query": ""}, follow=True)
        self.assertEqual(response.status_code, 200)
        for page in self.content_owner_pages:
            self.assertNotContains(response, page.title)
        for page in self.pages:
            self.assertNotContains(response, page.title)
        for person in self.people:
            self.assertNotContains(response, person.email)
        for team in self.teams:
            self.assertNotContains(response, team.name)

        self.assertContains(response, "All&nbsp;(0)")
        self.assertContains(response, "People&nbsp;(0)")
        self.assertContains(response, "Teams&nbsp;(0)")
        self.assertContains(response, "Guidance&nbsp;(0)")
        self.assertContains(response, "Tools&nbsp;(0)")
        self.assertContains(response, "News&nbsp;(0)")
        self.assertContains(response, "0 pages")
        self.assertContains(response, "0 people")
        self.assertContains(response, "0 teams")
        self.assertContains(response, "There are no matching pages.")
        self.assertContains(response, "There are no matching people.")
        self.assertContains(response, "There are no matching teams.")

    def test_fruits_all(self):
        response = self.client.get("/search/", {"query": "fruit"}, follow=True)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "All&nbsp;(7)")
        self.assertContains(response, "People&nbsp;(1)")
        self.assertContains(response, "Teams&nbsp;(1)")
        self.assertContains(response, "Guidance&nbsp;(2)")
        self.assertContains(response, "Tools&nbsp;(1)")
        self.assertContains(response, "News&nbsp;(1)")
        self.assertContains(response, "5 pages")
        self.assertContains(response, "1 person")
        self.assertContains(response, "1 team")
        self.assertContains(response, "How to eat Fruit")
        self.assertContains(response, "What fruit can I eat?")
        self.assertContains(response, "How do I find fruit?")
        self.assertContains(response, "Fruit finder")
        self.assertContains(response, "Big fruit news")
        self.assertNotContains(response, "An irrelevant page")
        self.assertNotContains(response, "Policies not relating to food")
        self.assertNotContains(response, "How to write test parent")
        self.assertNotContains(response, "Internal tooling tool")
        self.assertNotContains(response, "New news")
        self.assertContains(response, "Martin Fruit")
        self.assertNotContains(response, "Adam Ant")
        self.assertContains(response, "Fruit pickers")
        self.assertNotContains(response, "Middle managers")

    def test_fruits_news(self):
        response = self.client.get("/search/news/", {"query": "fruit"}, follow=True)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "All&nbsp;(7)")
        self.assertContains(response, "People&nbsp;(1)")
        self.assertContains(response, "Teams&nbsp;(1)")
        self.assertContains(response, "Guidance&nbsp;(2)")
        self.assertContains(response, "Tools&nbsp;(1)")
        self.assertContains(response, "News&nbsp;(1)")
        self.assertNotContains(response, "How to eat Fruit")
        self.assertNotContains(response, "What fruit can I eat?")
        self.assertNotContains(response, "How do I find fruit?")
        self.assertNotContains(response, "Fruit finder")
        self.assertContains(response, "Big fruit news")
        self.assertNotContains(response, "An irrelevant page")
        self.assertNotContains(response, "Policies not relating to food")
        self.assertNotContains(response, "How to write test parent")
        self.assertNotContains(response, "Internal tooling tool")
        self.assertNotContains(response, "New news")
        self.assertNotContains(response, "Martin Fruit")
        self.assertNotContains(response, "Adam Ant")
        self.assertNotContains(response, "Fruit pickers")
        self.assertNotContains(response, "Middle managers")

    def test_fruits_tools(self):
        response = self.client.get("/search/tools/", {"query": "fruit"}, follow=True)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "All&nbsp;(7)")
        self.assertContains(response, "People&nbsp;(1)")
        self.assertContains(response, "Teams&nbsp;(1)")
        self.assertContains(response, "Guidance&nbsp;(2)")
        self.assertContains(response, "Tools&nbsp;(1)")
        self.assertContains(response, "News&nbsp;(1)")
        self.assertNotContains(response, "How to eat Fruit")
        self.assertNotContains(response, "What fruit can I eat?")
        self.assertNotContains(response, "How do I find fruit?")
        self.assertContains(response, "Fruit finder")
        self.assertNotContains(response, "Big fruit news")
        self.assertNotContains(response, "An irrelevant page")
        self.assertNotContains(response, "Policies not relating to food")
        self.assertNotContains(response, "How to write test parent")
        self.assertNotContains(response, "Internal tooling tool")
        self.assertNotContains(response, "New news")
        self.assertNotContains(response, "Martin Fruit")
        self.assertNotContains(response, "Adam Ant")
        self.assertNotContains(response, "Fruit pickers")
        self.assertNotContains(response, "Middle managers")

    def test_fruits_guidance(self):
        response = self.client.get("/search/guidance/", {"query": "fruit"}, follow=True)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "All&nbsp;(7)")
        self.assertContains(response, "People&nbsp;(1)")
        self.assertContains(response, "Teams&nbsp;(1)")
        self.assertContains(response, "Guidance&nbsp;(2)")
        self.assertContains(response, "Tools&nbsp;(1)")
        self.assertContains(response, "News&nbsp;(1)")
        self.assertContains(response, "How to eat Fruit")
        self.assertContains(response, "What fruit can I eat?")
        self.assertNotContains(response, "How do I find fruit?")
        self.assertNotContains(response, "Fruit finder")
        self.assertNotContains(response, "Big fruit news")
        self.assertNotContains(response, "An irrelevant page")
        self.assertNotContains(response, "Policies not relating to food")
        self.assertNotContains(response, "How to write test parent")
        self.assertNotContains(response, "Internal tooling tool")
        self.assertNotContains(response, "New news")
        self.assertNotContains(response, "Martin Fruit")
        self.assertNotContains(response, "Adam Ant")
        self.assertNotContains(response, "Fruit pickers")
        self.assertNotContains(response, "Middle managers")

    def test_fruits_teams(self):
        response = self.client.get("/search/teams/", {"query": "fruit"}, follow=True)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "All&nbsp;(7)")
        self.assertContains(response, "People&nbsp;(1)")
        self.assertContains(response, "Teams&nbsp;(1)")
        self.assertContains(response, "Guidance&nbsp;(2)")
        self.assertContains(response, "Tools&nbsp;(1)")
        self.assertContains(response, "News&nbsp;(1)")
        self.assertNotContains(response, "How to eat Fruit")
        self.assertNotContains(response, "What fruit can I eat?")
        self.assertNotContains(response, "How do I find fruit?")
        self.assertNotContains(response, "Fruit finder")
        self.assertNotContains(response, "Big fruit news")
        self.assertNotContains(response, "An irrelevant page")
        self.assertNotContains(response, "Policies not relating to food")
        self.assertNotContains(response, "How to write test parent")
        self.assertNotContains(response, "Internal tooling tool")
        self.assertNotContains(response, "New news")
        self.assertNotContains(response, "Martin Fruit")
        self.assertNotContains(response, "Adam Ant")
        self.assertContains(response, "Fruit pickers")
        self.assertNotContains(response, "Middle managers")

    def test_fruits_people(self):
        response = self.client.get("/search/people/", {"query": "fruit"}, follow=True)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "All&nbsp;(7)")
        self.assertContains(response, "People&nbsp;(1)")
        self.assertContains(response, "Teams&nbsp;(1)")
        self.assertContains(response, "Guidance&nbsp;(2)")
        self.assertContains(response, "Tools&nbsp;(1)")
        self.assertContains(response, "News&nbsp;(1)")
        self.assertNotContains(response, "How to eat Fruit")
        self.assertNotContains(response, "What fruit can I eat?")
        self.assertNotContains(response, "How do I find fruit?")
        self.assertNotContains(response, "Fruit finder")
        self.assertNotContains(response, "Big fruit news")
        self.assertNotContains(response, "An irrelevant page")
        self.assertNotContains(response, "Policies not relating to food")
        self.assertNotContains(response, "How to write test parent")
        self.assertNotContains(response, "Internal tooling tool")
        self.assertNotContains(response, "New news")
        self.assertContains(response, "Martin Fruit")
        self.assertNotContains(response, "Adam Ant")
        self.assertNotContains(response, "Fruit pickers")
        self.assertNotContains(response, "Middle managers")


# Tests to check the sub-class overriding works as expected - in their own file because they mess wih models

import pytest
from django.conf import settings
from django.db import models

from wagtail.search.backends import get_search_backend
from wagtail.search.index import AutocompleteField, SearchField

from extended_search.settings import settings_singleton
from extended_search.index import DWIndexedField as IndexedField
from extended_search.models import Setting

from testapp.models import IndexedModel, ChildModel


class TestPerModelFieldOverrides:
    def get_search_mapping_for_updated_indexed_fields(
        self, model_class, indexed_fields, base_fields=None
    ):
        if base_fields is None:
            base_fields = []

        backend_name = settings.WAGTAILSEARCH_BACKENDS["default"]["BACKEND"]
        backend = get_search_backend(backend_name)

        model_class.processed_search_fields = {}  # kills get_search_fields cache
        model_class.indexed_fields = indexed_fields
        model_class.search_fields = base_fields
        index = backend.get_index_for_model(model_class)
        mapping_cls = index.mapping_class(model_class)

        settings_singleton.initialise_field_dict()

        return mapping_cls.get_mapping()

    def count_matching_search_autocomplete_fields(self, model_class, name):
        count = 0
        for field in model_class.get_search_fields(ignore_cache=True):
            if name in field.field_name and (  # catch variants like "_explicit"
                isinstance(field, SearchField) or isinstance(field, AutocompleteField)
            ):
                count += 1
        return count

    def test_minimal_subclass_overrides_maximal_baseclass(self):
        parent_mapping = self.get_search_mapping_for_updated_indexed_fields(
            IndexedModel,
            [
                IndexedField(
                    "title",
                    search=True,
                    autocomplete=True,
                ),
            ],
        )
        child_mapping = self.get_search_mapping_for_updated_indexed_fields(
            ChildModel,
            [
                IndexedField(
                    "title",
                    search=True,
                ),
            ],
            IndexedModel.search_fields,
        )

        assert (
            self.count_matching_search_autocomplete_fields(IndexedModel, "title") == 2
        )
        assert self.count_matching_search_autocomplete_fields(ChildModel, "title") == 1

        assert "testapp_indexedmodel__title" in parent_mapping["properties"]
        assert "testapp_childmodel__title" in child_mapping["properties"]
        assert "testapp_indexedmodel__title_edgengrams" in parent_mapping["properties"]
        assert (
            "testapp_indexedmodel__title_edgengrams" not in child_mapping["properties"]
        )
        assert "testapp_childmodel__title_edgengrams" not in child_mapping["properties"]

    def test_maximal_subclass_overrides_minimal_baseclass(self):
        parent_mapping = self.get_search_mapping_for_updated_indexed_fields(
            IndexedModel,
            [
                IndexedField(
                    "title",
                    search=True,
                ),
            ],
        )
        child_mapping = self.get_search_mapping_for_updated_indexed_fields(
            ChildModel,
            [
                IndexedField(
                    "title",
                    search=True,
                    autocomplete=True,
                ),
            ],
            IndexedModel.search_fields,
        )

        assert (
            self.count_matching_search_autocomplete_fields(IndexedModel, "title") == 1
        )
        assert self.count_matching_search_autocomplete_fields(ChildModel, "title") == 2

        assert "testapp_indexedmodel__title" in parent_mapping["properties"]
        assert "testapp_childmodel__title" in child_mapping["properties"]
        assert (
            "testapp_indexedmodel__title_edgengrams" not in parent_mapping["properties"]
        )
        assert "testapp_childmodel__title_edgengrams" in child_mapping["properties"]

    def test_subclass_overrides_boost(self):
        parent_mapping = self.get_search_mapping_for_updated_indexed_fields(
            IndexedModel,
            [
                IndexedField(
                    "title",
                    search=True,
                    boost=5.0,
                ),
            ],
        )
        child_mapping = self.get_search_mapping_for_updated_indexed_fields(
            ChildModel,
            [
                IndexedField(
                    "title",
                    search=True,
                    boost=10.0,
                ),
            ],
            IndexedModel.search_fields,
        )

        # @TODO hopefully we can get a better boost indicator
        for field_name, field_details in parent_mapping["properties"].items():
            if "title" in field_name:
                assert "_all_text_boost_10_0" not in field_details["copy_to"]
                assert "_all_text_boost_5_0" in field_details["copy_to"]

        for field_name, field_details in child_mapping["properties"].items():
            if "title" in field_name:
                assert "_all_text_boost_10_0" in field_details["copy_to"]
                assert "_all_text_boost_5_0" not in field_details["copy_to"]

    @pytest.mark.django_db
    def test_subclass_settings_overrides_work_only_on_subclass(self):
        self.get_search_mapping_for_updated_indexed_fields(
            IndexedModel,
            [
                IndexedField(
                    "title",
                    search=True,
                    boost=5.0,
                ),
            ],
        )
        self.get_search_mapping_for_updated_indexed_fields(
            ChildModel,
            [
                IndexedField(
                    "title",
                    search=True,
                    boost=10.0,
                ),
            ],
            IndexedModel.search_fields,
        )
        search_settings = settings_singleton.to_dict()

        parent_field_key = "testapp.indexedmodel.title"
        child_field_key = "testapp.childmodel.title"

        assert search_settings["boost_parts"]["fields"][parent_field_key] == 5.0
        assert search_settings["boost_parts"]["fields"][child_field_key] == 10.0

        instance = SearchSettings()
        instance.initialise_db_dict()
        Setting.objects.create(
            key=f"boost_parts__fields__{child_field_key}", value=100.5
        )
        assert Setting.objects.all().count() == 1
        instance.initialise_db_dict()

        search_settings = settings_singleton.to_dict()
        assert search_settings["boost_parts"]["fields"][child_field_key] == str(100.5)
