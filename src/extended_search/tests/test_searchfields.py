from wagtail.search import index

from extended_search.index import (
    AutocompleteField,
    BaseField,
    FilterField,
    IndexedField,
    ModelFieldNameMixin,
    RelatedFields,
    SearchField,
)


class CustomObject:
    bar = "baz"

    def call_baz(self):
        return "called_baz"


class TestBaseField:
    def test_get_field_uses_model_field_name(self, mocker):
        mock_model = mocker.Mock()
        mock_model._meta.get_field.return_value = None
        original_field = index.BaseField("foo")
        original_field.get_field(mock_model)
        mock_model._meta.get_field.assert_called_once_with("foo")

        mock_model.reset_mock()
        field = BaseField("foo", model_field_name="bar")
        field.get_field(mock_model)
        mock_model._meta.get_field.assert_called_once_with("bar")

    def test_get_field_uses_parent(self, mocker):
        mock_model = mocker.Mock()
        mock_model._meta.get_field.return_value = None
        parent_method = mocker.patch(
            "wagtail.search.index.BaseField.get_field", return_value=True
        )
        field = BaseField("foo", model_field_name="bar")
        returned_field = field.get_field(mock_model)
        parent_method.assert_not_called()
        assert returned_field is None

        mock_model._meta.get_field.return_value = "foobar"
        field = BaseField("foo")
        returned_field = field.get_field(mock_model)
        parent_method.assert_not_called()
        assert returned_field == "foobar"

    def test_get_attname_uses_field_name_not_model_field_name(self, mocker):
        mock_field = mocker.Mock()
        mock_field.attname = "baz"
        mock_model = mocker.Mock()
        mock_model._meta.get_field.return_value = mock_field

        original_field = index.BaseField("foo")
        assert original_field.get_attname(mock_model) == "baz"

        field = BaseField("foo")
        assert field.get_attname(mock_model) == "baz"

        field = BaseField("foo", model_field_name="bar")
        assert field.field_name == "foo"
        assert field.model_field_name == "bar"
        assert field.get_attname(mock_model) == "foo"

    def test_get_attname_uses_parent(self, mocker):
        mock_model = mocker.Mock()
        parent_method = mocker.patch(
            "wagtail.search.index.BaseField.get_attname", return_value=True
        )
        field = BaseField("foo", model_field_name="bar")
        field.get_attname(mock_model)
        parent_method.assert_not_called()

        field = BaseField("foo")
        field.get_attname(mock_model)
        parent_method.assert_called_once()

    def test_get_definition_model_uses_parent_and_model_field_name(self, mocker):
        mock_model = mocker.Mock()
        parent_method = mocker.patch(
            "wagtail.search.index.BaseField.get_definition_model", return_value="foobar"
        )
        field = BaseField("foo")
        result = field.get_definition_model(mock_model)
        parent_method.assert_called_once()
        parent_method.assert_called_with(mock_model)
        assert result == parent_method.return_value

        parent_method.return_value = None
        mocker.patch("inspect.getmro", return_value=[CustomObject])
        assert field.get_definition_model(mock_model) is None

        field = BaseField("foo", model_field_name="bar")
        result = field.get_definition_model(mock_model)
        assert result == CustomObject

    def test_get_value_uses_parent_and_model_field_name(self, mocker):
        parent_method = mocker.patch(
            "wagtail.search.index.BaseField.get_value",
            return_value="foobar",
        )
        field = BaseField("foo")
        assert field.model_field_name == "foo"
        result = field.get_value(CustomObject())
        parent_method.assert_called_once()
        assert result == "foobar"

        parent_method.return_value = None
        field = BaseField("foo", model_field_name="bar")
        result = field.get_value(CustomObject())
        assert result == "baz"

        field = BaseField("foo", model_field_name="other")
        result = field.get_value(CustomObject())
        assert result is None

    def test_extends_renamedfieldmixin(self):
        assert issubclass(BaseField, ModelFieldNameMixin)
        assert issubclass(BaseField, index.BaseField)

    def test_get_value_doesnt_call_callable(self, mocker):
        mocker.patch(
            "wagtail.search.index.BaseField.get_value",
            return_value=None,
        )
        obj = CustomObject()
        field = BaseField("foo", model_field_name="call_baz")
        result = field.get_value(obj)
        assert result == obj.call_baz


class TestAutocompleteField:
    def test_extends_renamedfieldmixin(self):
        assert issubclass(AutocompleteField, ModelFieldNameMixin)
        assert issubclass(AutocompleteField, BaseField)
        assert issubclass(AutocompleteField, index.AutocompleteField)


class TestSearchField:
    def test_extends_renamedfieldmixin(self):
        assert issubclass(SearchField, ModelFieldNameMixin)
        assert issubclass(AutocompleteField, BaseField)
        assert issubclass(SearchField, index.SearchField)


class TestFilterField:
    def test_extends_renamedfieldmixin(self):
        assert issubclass(FilterField, ModelFieldNameMixin)
        assert issubclass(AutocompleteField, BaseField)
        assert issubclass(FilterField, index.FilterField)


class TestRelatedFields:
    def test_extends_renamedfieldmixin(self):
        assert issubclass(RelatedFields, ModelFieldNameMixin)
        assert issubclass(RelatedFields, index.RelatedFields)


class TestIndexedField:
    def test_extends_renamedfieldmixin(self):
        assert issubclass(IndexedField, ModelFieldNameMixin)
        assert issubclass(IndexedField, BaseField)
