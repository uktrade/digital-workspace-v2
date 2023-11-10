from wagtail.search import index

from extended_search.index import (
    AutocompleteField,
    RelatedFields,
    RenamedFieldMixin,
    SearchField,
)


class TestRenamedFieldMixin:
    def test_get_field_uses_model_field_name(self, mocker):
        mock_model = mocker.Mock()
        mock_model._meta.get_field.return_value = None
        original_field = index.SearchField("foo")
        original_field.get_field(mock_model)
        mock_model._meta.get_field.assert_called_once_with("foo")

        mock_model.reset_mock()
        field = SearchField("foo", model_field_name="bar")
        field.get_field(mock_model)
        mock_model._meta.get_field.assert_called_once_with("bar")

    def test_get_field_uses_parent(self, mocker):
        mock_model = mocker.Mock()
        mock_model._meta.get_field.return_value = None
        parent_method = mocker.patch(
            "wagtail.search.index.SearchField.get_field", return_value=True
        )
        field = SearchField("foo", model_field_name="bar")
        field.get_field(mock_model)
        parent_method.assert_not_called()

        field = SearchField("foo")
        field.get_field(mock_model)
        parent_method.assert_called_once()

    def test_get_attname_uses_field_name_not_model_field_name(self, mocker):
        mock_field = mocker.Mock()
        mock_field.attname = "baz"
        mock_model = mocker.Mock()
        mock_model._meta.get_field.return_value = mock_field

        original_field = index.SearchField("foo")
        assert original_field.get_attname(mock_model) == "baz"

        field = SearchField("foo")
        assert field.get_attname(mock_model) == "baz"

        field = SearchField("foo", model_field_name="bar")
        assert field.field_name == "foo"
        assert field.kwargs["model_field_name"] == "bar"
        assert field.get_attname(mock_model) == "foo"

    def test_get_attname_uses_parent(self, mocker):
        mock_model = mocker.Mock()
        parent_method = mocker.patch(
            "wagtail.search.index.SearchField.get_attname", return_value=True
        )
        field = SearchField("foo", model_field_name="bar")
        field.get_attname(mock_model)
        parent_method.assert_not_called()

        field = SearchField("foo")
        field.get_attname(mock_model)
        parent_method.assert_called_once()

    def test_get_definition_model_uses_parent_and_model_field_name(self, mocker):
        mock_model = mocker.Mock()
        parent_method = mocker.patch(
            "wagtail.search.index.SearchField.get_definition_model", return_value=None
        )
        mock_model.IndexManager.is_directly_defined.return_value = False
        field = SearchField("foo")
        result = field.get_definition_model(mock_model)
        parent_method.assert_called_once()
        assert result is None

        parent_method.reset_mock()
        mock_model.IndexManager.is_directly_defined.return_value = True
        assert field.get_definition_model(mock_model) == mock_model
        parent_method.assert_not_called()

        mock_model.IndexManager.is_directly_defined.return_value = False
        mock_base = mocker.Mock()
        mock_base.bar = True
        mocker.patch("inspect.getmro", return_value=[mock_base])
        field = SearchField("foo", model_field_name="bar")
        result = field.get_definition_model(mock_model)
        assert result == mock_base

    def test_get_value_uses_parent_and_model_field_name(self, mocker):
        mock_model = mocker.Mock()
        mock_model.bar = "baz"
        parent_method = mocker.patch(
            "wagtail.search.index.SearchField.get_value", return_value=None
        )
        field = SearchField("foo")
        result = field.get_value(mock_model)
        parent_method.assert_called_once()
        assert result is None

        field = SearchField("foo", model_field_name="bar")
        result = field.get_value(mock_model)
        assert result == "baz"


class TestAutocompleteField:
    def test_extends_renamedfieldmixin(self):
        assert issubclass(AutocompleteField, RenamedFieldMixin)
        assert issubclass(AutocompleteField, index.AutocompleteField)


class TestSearchField:
    def test_extends_renamedfieldmixin(self):
        assert issubclass(SearchField, RenamedFieldMixin)
        assert issubclass(SearchField, index.SearchField)


class TestRelatedFields:
    def test_extends_renamedfieldmixin(self):
        assert issubclass(RelatedFields, RenamedFieldMixin)
        assert issubclass(RelatedFields, index.RelatedFields)
