import json

from wagtail.documents.models import Document
from wagtail.images.models import Image
from wagtail.models import Page
from wagtailmedia.models import Media

from about_us.models import AboutUs, AboutUsHome
from content.models import BasePage, BlogIndex, BlogPost, ContentPage, NavigationPage
from core.models.tags import Tag
from country_fact_sheet.models import CountryFactSheetHome
from events.models import EventPage, EventsHome
from extended_search.index import DWIndexedField, class_is_indexed, get_indexed_models
from extended_search.management.commands.create_index_fields_json import (
    JSON_FILE,
    get_indexed_models_and_fields_dict,
)
from home.models import HomePage
from networks.models import Network, NetworkContentPage, NetworksHome
from news.models import NewsHome, NewsPage
from peoplefinder.models import Person, Team
from testapp.models import (
    AbstractIndexedModel,
    AbstractModel,
    ChildModel,
    IndexedModel,
    InheritedStandardIndexedModel,
    InheritedStandardIndexedModelWithChanges,
    InheritedStandardIndexedModelWithChangesWithScoreFunction,
    Model,
    StandardIndexedModel,
    StandardIndexedModelWithScoreFunction,
    StandardIndexedModelWithScoreFunctionOriginFifty,
)
from tools.models import Tool, ToolsHome
from working_at_dit.models import (
    Guidance,
    GuidanceHome,
    HowDoI,
    HowDoIHome,
    PageWithTopics,
    PoliciesAndGuidanceHome,
    PoliciesHome,
    Policy,
    Topic,
    TopicHome,
    WorkingAtDITHome,
)


class TestIndexed:
    def test_get_indexed_fields(self):
        indexed_fields = StandardIndexedModel.get_indexed_fields()
        assert isinstance(indexed_fields, list)
        assert len(indexed_fields) == 1
        assert isinstance(indexed_fields[0], DWIndexedField)
        assert indexed_fields[0].autocomplete is False
        assert indexed_fields[0].autocomplete_kwargs == {}
        assert indexed_fields[0].boost == 5.0
        assert indexed_fields[0].explicit
        assert indexed_fields[0].field_name == "title"
        assert indexed_fields[0].filter is False
        assert indexed_fields[0].filter_kwargs == {}
        assert indexed_fields[0].fuzzy
        assert indexed_fields[0].keyword is False
        assert indexed_fields[0].model_field_name == "title"
        assert indexed_fields[0].parent_field is None
        assert indexed_fields[0].search
        assert indexed_fields[0].search_kwargs == {}
        assert indexed_fields[0].tokenized

        indexed_fields = InheritedStandardIndexedModelWithChanges.get_indexed_fields()
        assert isinstance(indexed_fields, list)
        assert len(indexed_fields) == 1
        assert isinstance(indexed_fields[0], DWIndexedField)
        assert indexed_fields[0].autocomplete is False
        assert indexed_fields[0].autocomplete_kwargs == {}
        assert indexed_fields[0].boost == 50.0
        assert indexed_fields[0].explicit is False
        assert indexed_fields[0].field_name == "title"
        assert indexed_fields[0].filter is False
        assert indexed_fields[0].filter_kwargs == {}
        assert indexed_fields[0].fuzzy is False
        assert indexed_fields[0].keyword is False
        assert indexed_fields[0].model_field_name == "title"
        assert indexed_fields[0].parent_field is None
        assert indexed_fields[0].search
        assert indexed_fields[0].search_kwargs == {}
        assert indexed_fields[0].tokenized

    def test_get_indexed_fields_as_dict(self):
        indexed_fields = StandardIndexedModel.get_indexed_fields(as_dict=True)
        assert isinstance(indexed_fields, dict)
        assert "title" in indexed_fields
        assert len(indexed_fields["title"]) == 1
        assert isinstance(indexed_fields["title"][0], DWIndexedField)
        assert indexed_fields["title"][0].autocomplete is False
        assert indexed_fields["title"][0].autocomplete_kwargs == {}
        assert indexed_fields["title"][0].boost == 5.0
        assert indexed_fields["title"][0].explicit
        assert indexed_fields["title"][0].field_name == "title"
        assert indexed_fields["title"][0].filter is False
        assert indexed_fields["title"][0].filter_kwargs == {}
        assert indexed_fields["title"][0].fuzzy
        assert indexed_fields["title"][0].keyword is False
        assert indexed_fields["title"][0].model_field_name == "title"
        assert indexed_fields["title"][0].parent_field is None
        assert indexed_fields["title"][0].search
        assert indexed_fields["title"][0].search_kwargs == {}
        assert indexed_fields["title"][0].tokenized

        indexed_fields = InheritedStandardIndexedModelWithChanges.get_indexed_fields(
            as_dict=True
        )
        assert isinstance(indexed_fields, dict)
        assert "title" in indexed_fields
        assert len(indexed_fields["title"]) == 1
        assert isinstance(indexed_fields["title"][0], DWIndexedField)
        assert indexed_fields["title"][0].autocomplete is False
        assert indexed_fields["title"][0].autocomplete_kwargs == {}
        assert indexed_fields["title"][0].boost == 50.0
        assert indexed_fields["title"][0].explicit is False
        assert indexed_fields["title"][0].field_name == "title"
        assert indexed_fields["title"][0].filter is False
        assert indexed_fields["title"][0].filter_kwargs == {}
        assert indexed_fields["title"][0].fuzzy is False
        assert indexed_fields["title"][0].keyword is False
        assert indexed_fields["title"][0].model_field_name == "title"
        assert indexed_fields["title"][0].parent_field is None
        assert indexed_fields["title"][0].search
        assert indexed_fields["title"][0].search_kwargs == {}
        assert indexed_fields["title"][0].tokenized

    def test_generate_from_indexed_fields(self):
        processed_index_fields = StandardIndexedModel.generate_from_indexed_fields()
        assert isinstance(processed_index_fields, dict)
        assert "title" in processed_index_fields
        assert len(processed_index_fields["title"]) == 2
        processed_index_field_names = [
            f.field_name for f in processed_index_fields["title"]
        ]
        assert "title" in processed_index_field_names
        assert "title_explicit" in processed_index_field_names

        processed_index_fields = (
            InheritedStandardIndexedModelWithChanges.generate_from_indexed_fields()
        )
        assert isinstance(processed_index_fields, dict)
        assert "title" in processed_index_fields
        assert len(processed_index_fields["title"]) == 1
        processed_index_field_names = [
            f.field_name for f in processed_index_fields["title"]
        ]
        assert "title" in processed_index_field_names
        assert "title_explicit" not in processed_index_field_names

    def test_get_search_fields(self):
        search_fields = StandardIndexedModel.get_search_fields(ignore_cache=True)
        assert isinstance(search_fields, list)
        assert len(search_fields) == 2
        search_fields_field_names = [f.field_name for f in search_fields]
        assert "title" in search_fields_field_names
        assert "title_explicit" in search_fields_field_names

        search_fields = InheritedStandardIndexedModelWithChanges.get_search_fields(
            ignore_cache=True
        )
        assert isinstance(search_fields, list)
        assert len(search_fields) == 1
        search_fields_field_names = [f.field_name for f in search_fields]
        assert "title" in search_fields_field_names
        assert "title_explicit" not in search_fields_field_names

    def test_get_search_fields_with_cache(self, mocker):
        mock_parent_get_search_fields = mocker.patch(
            "wagtail.search.index.Indexed.get_search_fields"
        )

        StandardIndexedModel.processed_search_fields = {}
        search_fields = StandardIndexedModel.get_search_fields()
        mock_parent_get_search_fields.assert_called_once_with()
        assert StandardIndexedModel in StandardIndexedModel.processed_search_fields
        assert (
            StandardIndexedModel.processed_search_fields[StandardIndexedModel]
            == search_fields
        )

        mock_parent_get_search_fields.reset_mock()
        search_fields = StandardIndexedModel.get_search_fields()
        mock_parent_get_search_fields.assert_not_called()

        mock_parent_get_search_fields.reset_mock()
        search_fields = StandardIndexedModel.get_search_fields(ignore_cache=True)
        mock_parent_get_search_fields.assert_called_once_with()

    def test_has_unique_index_fields(self, mocker):
        assert StandardIndexedModel.has_unique_index_fields()
        assert not InheritedStandardIndexedModel.has_unique_index_fields()
        assert InheritedStandardIndexedModelWithChanges.has_unique_index_fields()


class TestModuleFunctions:
    def test_get_indexed_models(self, mocker):
        mock_model_1 = Model
        mock_model_2 = AbstractModel
        mock_model_3 = IndexedModel
        mock_model_4 = AbstractIndexedModel
        mock_get_models = mocker.patch(
            "extended_search.index.apps.get_models",
            return_value=[
                mock_model_1,
                mock_model_2,
                mock_model_3,
                mock_model_4,
            ],
        )

        indexed_models = get_indexed_models()

        mock_get_models.assert_called_once()
        assert mock_model_1 not in indexed_models
        assert mock_model_2 not in indexed_models
        assert mock_model_3 in indexed_models
        assert mock_model_4 not in indexed_models

    def test_class_is_indexed(self):
        assert not class_is_indexed(Model)
        assert not class_is_indexed(AbstractModel)
        assert class_is_indexed(IndexedModel)
        assert not class_is_indexed(AbstractIndexedModel)


class TestProject:
    def test_indexed_models(self):
        assert set(get_indexed_models()) == {
            IndexedModel,
            ChildModel,
            StandardIndexedModel,
            InheritedStandardIndexedModel,
            InheritedStandardIndexedModelWithChanges,
            StandardIndexedModelWithScoreFunction,
            StandardIndexedModelWithScoreFunctionOriginFifty,
            InheritedStandardIndexedModelWithChangesWithScoreFunction,
            HomePage,
            BasePage,
            ContentPage,
            NavigationPage,
            EventsHome,
            EventPage,
            NewsPage,
            NewsHome,
            WorkingAtDITHome,
            Topic,
            TopicHome,
            PageWithTopics,
            HowDoI,
            HowDoIHome,
            Guidance,
            Policy,
            PoliciesHome,
            GuidanceHome,
            PoliciesAndGuidanceHome,
            Tool,
            ToolsHome,
            AboutUs,
            AboutUsHome,
            NetworksHome,
            Network,
            NetworkContentPage,
            CountryFactSheetHome,
            BlogIndex,
            BlogPost,
            Tag,
            Person,
            Team,
            Document,
            Image,
            Page,
            Media,
        }, "Indexed models have changed, please update this test if this was intentional."

    def test_indexed_models_and_fields(test):
        with open(JSON_FILE, "r") as f:
            expected_indexed_models_and_fields = json.load(f)
            assert (
                get_indexed_models_and_fields_dict()
                == expected_indexed_models_and_fields
            ), (
                "Indexed models and fields have changed."
                " If this was intentional, please update the JSON file by running the"
                " `create_index_fields_json` management command."
            )
