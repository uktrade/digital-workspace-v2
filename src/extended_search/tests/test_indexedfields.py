import pytest
from django.core.exceptions import FieldDoesNotExist
from django.db.models.fields.related import ForeignObjectRel, OneToOneRel, RelatedField
from modelcluster.fields import ParentalManyToManyField
from wagtail.search import index

from extended_search import settings
from extended_search.index import (
    AutocompleteField,
    BaseField,
    DWIndexedField,
    FilterField,
    IndexedField,
    ModelFieldNameMixin,
    MultiQueryIndexedField,
    RelatedFields,
    SearchField,
    get_indexed_field_name,
)
from extended_search.tests.testing_classes import MixedIn
from extended_search.types import AnalysisType


class RelatedParentalM2M(ParentalManyToManyField, RelatedField): ...


class ForeignO2O(OneToOneRel, ForeignObjectRel): ...


class TestModelFieldNameMixin:
    def test_init_params_accepted_defaults_and_all_saved(self):
        field = MixedIn("foo")
        assert field.model_field_name == "foo"
        assert field.parent_field is None

        field = MixedIn("foo", model_field_name="bar")
        assert field.model_field_name == "bar"
        assert field.parent_field is None

        field = MixedIn("foo", model_field_name="bar", parent_field="baz")
        assert field.model_field_name == "bar"
        assert field.parent_field == "baz"

    def test_get_field(self, mocker):
        mock_model_class = mocker.Mock()
        mock_model_class._meta.get_field.return_value = "baz"

        field = MixedIn("foo")
        assert field.get_field(mock_model_class) == "baz"
        mock_model_class._meta.get_field.assert_called_once_with("foo")
        mock_model_class._meta.get_field.reset_mock()

        field = MixedIn("foo", model_field_name="bar")
        assert field.get_field(mock_model_class) == "baz"
        mock_model_class._meta.get_field.assert_called_once_with("bar")

    def test_get_definition_model(self, mocker):
        parent_model_class = mocker.Mock()
        parent_model_class.foobar = 123
        mock_getmro = mocker.patch("inspect.getmro", return_value=[parent_model_class])

        mock_parent_get_definition_model = mocker.patch(
            "extended_search.tests.testing_classes.Base.get_definition_model",
            return_value=None,
        )
        mock_get_base_model_field_name = mocker.patch(
            "extended_search.index.ModelFieldNameMixin.get_base_model_field_name",
            return_value="foobar",
        )

        mock_model_class = mocker.Mock()

        mock_parent_get_definition_model.return_value = "foo"
        field = MixedIn("foo", configuration_model="bar")
        assert field.get_definition_model(mock_model_class) == "bar"
        mock_parent_get_definition_model.assert_not_called()
        mock_get_base_model_field_name.assert_not_called()
        mock_getmro.assert_not_called()

        field = MixedIn("foo")
        assert field.get_definition_model(mock_model_class) == "foo"
        mock_parent_get_definition_model.assert_called_once_with(mock_model_class)
        mock_parent_get_definition_model.reset_mock()
        mock_get_base_model_field_name.assert_not_called()
        mock_getmro.assert_not_called()

        mock_parent_get_definition_model.return_value = None
        field = MixedIn("foo")
        assert field.get_definition_model(mock_model_class) == parent_model_class
        mock_parent_get_definition_model.assert_called_once_with(mock_model_class)
        mock_getmro.assert_called_once_with(mock_model_class)
        mock_get_base_model_field_name.assert_called_once_with()
        mock_parent_get_definition_model.reset_mock()

    def test_get_value(self, mocker):
        mock_parent_get_value = mocker.patch(
            "extended_search.tests.testing_classes.Base.get_value",
            return_value="foo",
        )

        mock_model_class = mocker.Mock()
        mock_model_class.foo = None
        mock_model_class.bar = None

        field = MixedIn("foo")
        assert field.get_value(mock_model_class) == "foo"
        mock_parent_get_value.assert_called_once_with(mock_model_class)
        mock_parent_get_value.reset_mock()

        mock_parent_get_value.return_value = None
        field = MixedIn("foo")
        assert field.get_value(mock_model_class) is None
        mock_parent_get_value.assert_called_once_with(mock_model_class)
        mock_parent_get_value.reset_mock()

        field = MixedIn("foo", model_field_name="bar")
        assert field.get_value(mock_model_class) is None
        mock_parent_get_value.assert_called_once_with(mock_model_class)
        mock_parent_get_value.reset_mock()

        mock_model_class.foo = "baz"
        field = MixedIn("foo")
        assert field.get_value(mock_model_class) == "baz"
        mock_parent_get_value.assert_called_once_with(mock_model_class)
        mock_parent_get_value.reset_mock()

        mock_model_class.foo = None
        mock_model_class.bar = "baz"
        field = MixedIn("foo", model_field_name="bar")
        assert field.get_value(mock_model_class) == "baz"
        mock_parent_get_value.assert_called_once_with(mock_model_class)
        mock_parent_get_value.reset_mock()

    def test_is_relation_of(self):
        field = MixedIn("foo")
        assert field.parent_field is None

        field.is_relation_of("bar")
        assert field.parent_field == "bar"

        field.is_relation_of("baz")
        assert field.parent_field == "baz"

    def test_get_base_field(self, mocker):
        mock_parent_field = mocker.Mock()
        mock_parent_field.get_base_field = mocker.Mock(return_value="foo")

        field = MixedIn("foo")
        assert field.get_base_field() == field

        field.parent_field = mock_parent_field
        assert field.get_base_field() == "foo"
        mock_parent_field.get_base_field.assert_called_once_with()

    def test_get_base_model_field_name(self, mocker):
        mock_get_base_field = mocker.patch(
            "extended_search.index.ModelFieldNameMixin.get_base_field",
            return_value=MixedIn("bar", model_field_name="bazbar"),
        )

        field = MixedIn("foo")
        assert field.parent_field is None
        assert field.model_field_name == "foo"
        assert field.get_base_model_field_name() == "bazbar"
        mock_get_base_field.assert_called_once_with()

    def test_get_full_model_field_name(self, mocker):
        field = MixedIn("foo")
        assert field.get_full_model_field_name() == "foo"

        field = MixedIn("foo", model_field_name="bar")
        assert field.get_full_model_field_name() == "bar"

        field.parent_field = mocker.Mock()
        field.parent_field.get_full_model_field_name = mocker.Mock(
            return_value="baz",
        )
        assert field.get_full_model_field_name() == "baz.bar"


class TestBaseField:
    def test_init_params_accepted_defaults_and_all_saved(self):
        field = BaseField("foo")
        assert field.field_name == "foo"
        assert field.model_field_name == field.field_name
        assert field.parent_field is None

        field = BaseField("foo", model_field_name="bar")
        assert field.field_name == "foo"
        assert field.model_field_name == "bar"
        assert field.parent_field is None

        field = BaseField("foo", model_field_name="bar", parent_field="baz")
        assert field.field_name == "foo"
        assert field.model_field_name == "bar"
        assert field.parent_field == "baz"

    def test_basefield_inheritance(self):
        assert issubclass(BaseField, ModelFieldNameMixin)
        assert issubclass(BaseField, index.BaseField)


class TestSearchField:
    def test_searchfield_inheritance(self):
        assert issubclass(SearchField, BaseField)
        assert issubclass(SearchField, index.SearchField)
        assert issubclass(SearchField, index.BaseField)


class TestAutocompleteField:
    def test_autocompletefield_inheritance(self):
        assert issubclass(AutocompleteField, BaseField)
        assert issubclass(AutocompleteField, index.AutocompleteField)
        assert issubclass(AutocompleteField, index.BaseField)


class TestFilterField:
    def test_filterfield_inheritance(self):
        assert issubclass(FilterField, BaseField)
        assert issubclass(FilterField, index.FilterField)
        assert issubclass(FilterField, index.BaseField)


class TestRelatedFields:
    def test_init_params_accepted_defaults_and_all_saved(self):
        field = RelatedFields("foo", ["bar", "baz"])
        assert field.field_name == "foo"
        assert field.model_field_name == field.field_name
        assert field.fields == ["bar", "baz"]

    def test_relatedfields_inheritance(self):
        assert issubclass(RelatedFields, ModelFieldNameMixin)
        assert issubclass(RelatedFields, index.RelatedFields)

    def test_get_select_on_queryset(self, mocker):
        mock_qs = mocker.Mock()
        mock_qs.select_related.return_value = "--select-related--"
        mock_qs.prefetch_related.return_value = "--prefetch-related--"
        mock_get_field = mocker.patch("extended_search.index.RelatedFields.get_field")
        mock_field_m2o = mocker.Mock(spec=RelatedField)
        mock_field_m2o.many_to_one = True
        mock_field_m2o.one_to_one = False
        mock_field_m2o.one_to_many = False
        mock_field_m2o.many_to_many = False
        mock_field_o2o = mocker.Mock(spec=RelatedField)
        mock_field_o2o.many_to_one = False
        mock_field_o2o.one_to_one = True
        mock_field_o2o.one_to_many = False
        mock_field_o2o.many_to_many = False
        mock_field_o2m = mocker.Mock(spec=RelatedField)
        mock_field_o2m.many_to_one = False
        mock_field_o2m.one_to_one = False
        mock_field_o2m.one_to_many = True
        mock_field_o2m.many_to_many = False
        mock_field_m2m = mocker.Mock(spec=RelatedField)
        mock_field_m2m.many_to_one = False
        mock_field_m2m.one_to_one = False
        mock_field_m2m.one_to_many = False
        mock_field_m2m.many_to_many = True
        mock_field_parental = mocker.Mock(spec=RelatedParentalM2M)
        mock_field_forel = mocker.Mock(spec=ForeignObjectRel)
        mock_field_forel_o2orel = mocker.Mock(spec=ForeignO2O)
        field = RelatedFields("foo", [], model_field_name="bar")
        mock_get_field.side_effect = FieldDoesNotExist()

        assert field.select_on_queryset(mock_qs) == mock_qs
        mock_get_field.assert_called_once_with(mock_qs.model)
        mock_qs.select_related.assert_not_called()
        mock_qs.prefetch_related.assert_not_called()

        mock_get_field.side_effect = None
        mock_get_field.return_value = mock_field_m2o
        assert field.select_on_queryset(mock_qs) == "--select-related--"
        mock_qs.select_related.assert_called_once_with("bar")
        mock_qs.prefetch_related.assert_not_called()

        mock_qs.reset_mock()
        mock_get_field.return_value = mock_field_o2o
        assert field.select_on_queryset(mock_qs) == "--select-related--"
        mock_qs.select_related.assert_called_once_with("bar")
        mock_qs.prefetch_related.assert_not_called()

        mock_qs.reset_mock()
        mock_get_field.return_value = mock_field_o2m
        assert field.select_on_queryset(mock_qs) == "--prefetch-related--"
        mock_qs.select_related.assert_not_called()
        mock_qs.prefetch_related.assert_called_once_with("bar")

        mock_qs.reset_mock()
        mock_get_field.return_value = mock_field_m2m
        assert field.select_on_queryset(mock_qs) == "--prefetch-related--"
        mock_qs.select_related.assert_not_called()
        mock_qs.prefetch_related.assert_called_once_with("bar")

        mock_qs.reset_mock()
        mock_get_field.return_value = mock_field_parental
        assert field.select_on_queryset(mock_qs) == mock_qs
        mock_qs.select_related.assert_not_called()
        mock_qs.prefetch_related.assert_not_called()

        mock_qs.reset_mock()
        mock_get_field.return_value = mock_field_forel
        assert field.select_on_queryset(mock_qs) == "--prefetch-related--"
        mock_qs.select_related.assert_not_called()
        mock_qs.prefetch_related.assert_called_once_with("bar")

        mock_qs.reset_mock()
        mock_get_field.return_value = mock_field_forel_o2orel
        assert field.select_on_queryset(mock_qs) == "--select-related--"
        mock_qs.select_related.assert_called_once_with("bar")
        mock_qs.prefetch_related.assert_not_called()

    def test_generate_fields(self, mocker):
        mock_model = mocker.Mock()
        mock_relation = mocker.patch(
            "extended_search.index.RelatedFields.is_relation_of"
        )
        field = RelatedFields("foo", [], model_field_name="bar")
        assert field.fields == []
        generated_fields = field.generate_fields(cls=mock_model)
        assert len(generated_fields) == 1
        assert generated_fields[0].__dict__ == field.__dict__
        assert field.fields == []
        mock_relation.assert_not_called()

        parent_field = BaseField("dummy")
        generated_fields = field.generate_fields(
            cls=mock_model, parent_field=parent_field
        )
        assert len(generated_fields) == 1
        assert generated_fields[0].__dict__ == field.__dict__
        assert field.fields == []
        mock_relation.assert_called_once_with(parent_field)

        mock_ifield1 = mocker.Mock(spec=IndexedField)
        mock_ifield1.generate_fields.return_value = ["--search-field--"]
        mock_ifield2 = mocker.Mock(spec=IndexedField)
        mock_ifield2.generate_fields.return_value = ["--filter-field--"]
        field.fields = [mock_ifield1, mock_ifield2]
        generated_fields = field.generate_fields(cls=mock_model)
        assert len(generated_fields) == 1
        assert generated_fields[0].fields == ["--search-field--", "--filter-field--"]
        mock_ifield1.generate_fields.assert_called_once_with(
            mock_model, parent_field=field, configuration_model=None
        )
        mock_ifield2.generate_fields.assert_called_once_with(
            mock_model, parent_field=field, configuration_model=None
        )

        mock_rfield = mocker.Mock(spec=RelatedFields)
        mock_rfield.generate_fields.return_value = ["--related-field--"]
        field.fields = [mock_rfield, mock_ifield1]
        generated_fields = field.generate_fields(cls=mock_model)
        assert len(generated_fields) == 1
        assert generated_fields[0].fields == ["--related-field--", "--search-field--"]
        mock_rfield.generate_fields.assert_called_once_with(
            mock_model, parent_field=field, configuration_model=None
        )

        mock_sfield = mocker.Mock(spec=BaseField)
        field.fields = [mock_sfield, mock_ifield1]
        generated_fields = field.generate_fields(cls=mock_model)
        assert len(generated_fields) == 1
        assert generated_fields[0].fields == [mock_sfield, "--search-field--"]
        mock_sfield.is_relation_of.assert_called_once_with(field)

        field.fields = [mock_ifield2, mock_sfield, mock_rfield, mock_ifield1]
        generated_fields = field.generate_fields(cls=mock_model)
        assert len(generated_fields) == 1
        assert generated_fields[0].fields == [
            "--filter-field--",
            mock_sfield,
            "--related-field--",
            "--search-field--",
        ]


class TestIndexedField:
    def test_init_params_accepted_defaults_and_all_saved(self):
        field = IndexedField("foo")
        assert field.field_name == "foo"
        assert field.model_field_name == field.field_name
        assert field.boost == 1.0
        assert not field.search
        assert field.search_kwargs == {}
        assert not field.autocomplete
        assert field.autocomplete_kwargs == {}
        assert not field.filter
        assert field.filter_kwargs == {}

        field = IndexedField(
            "foo",
            boost=44.9,
            search=True,
            filter=True,
            autocomplete=True,
            search_kwargs={"foo": 99},
            filter_kwargs={"bar": True},
            autocomplete_kwargs={"baz": "foobar"},
        )
        assert field.boost == 44.9
        assert field.search
        assert field.search_kwargs == {"foo": 99}
        assert field.filter
        assert field.filter_kwargs == {"bar": True}
        assert field.autocomplete
        assert field.autocomplete_kwargs == {"baz": "foobar"}

    def test_generate_fields(self, mocker):
        mock_generate_search = mocker.patch(
            "extended_search.index.IndexedField.generate_search_fields",
            return_value=["--search-field--", "--search-field-2--"],
        )
        mock_generate_autocomplete = mocker.patch(
            "extended_search.index.IndexedField.generate_autocomplete_fields",
            return_value=["--autocomplete-field--"],
        )
        mock_generate_filter = mocker.patch(
            "extended_search.index.IndexedField.generate_filter_fields",
            return_value=["--filter-field--", "--filter-field-2--"],
        )
        mock_relation = mocker.patch(
            "extended_search.index.IndexedField.is_relation_of"
        )
        model = mocker.Mock()
        field = IndexedField("foo", model_field_name="bar")

        assert field.generate_fields(model) == []
        mock_generate_search.assert_not_called()
        mock_generate_autocomplete.assert_not_called()
        mock_generate_filter.assert_not_called()
        mock_relation.assert_not_called()

        parent_field = BaseField("dummy")
        assert field.generate_fields(model, parent_field=parent_field) == []
        mock_generate_search.assert_not_called()
        mock_generate_autocomplete.assert_not_called()
        mock_generate_filter.assert_not_called()
        mock_relation.assert_called_once_with(parent_field)

        field.search = True
        assert field.generate_fields(model) == [
            "--search-field--",
            "--search-field-2--",
        ]
        mock_generate_search.assert_called_once_with(model)
        mock_generate_autocomplete.assert_not_called()
        mock_generate_filter.assert_not_called()

        mock_generate_search.reset_mock()
        field.search = False
        field.autocomplete = True
        assert field.generate_fields(model) == ["--autocomplete-field--"]
        mock_generate_search.assert_not_called()
        mock_generate_autocomplete.assert_called_once_with(model)
        mock_generate_filter.assert_not_called()

        mock_generate_autocomplete.reset_mock()
        field.autocomplete = False
        field.filter = True
        assert field.generate_fields(model) == [
            "--filter-field--",
            "--filter-field-2--",
        ]
        mock_generate_search.assert_not_called()
        mock_generate_autocomplete.assert_not_called()
        mock_generate_filter.assert_called_once_with(model)

        mock_generate_filter.reset_mock()
        field.search = True
        field.autocomplete = True
        field.filter = True
        assert field.generate_fields(model) == [
            "--search-field--",
            "--search-field-2--",
            "--autocomplete-field--",
            "--filter-field--",
            "--filter-field-2--",
        ]
        mock_generate_search.assert_called_once_with(model)
        mock_generate_autocomplete.assert_called_once_with(model)
        mock_generate_filter.assert_called_once_with(model)

    def test_generate_search_fields(self, mocker):
        mock_get_variants = mocker.patch(
            "extended_search.index.IndexedField.get_search_field_variants",
            return_value=[],
        )
        mock_field = mocker.patch("extended_search.index.SearchField")
        model = mocker.Mock()
        field = IndexedField("foo", model_field_name="bar")

        assert field.generate_search_fields(model) == []

        mock_get_variants.return_value = [
            (("arg", "arg2"), {"kwarg": "value"}),
        ]
        result = field.generate_search_fields(model)
        assert len(result) == 1
        assert isinstance(result[0], mocker.MagicMock)
        mock_field.assert_called_once_with(
            "arg",
            "arg2",
            model_field_name="bar",
            boost=1.0,
            parent_field=None,
            configuration_model=None,
            kwarg="value",
        )

        mock_field.reset_mock()
        field.parent_field = "baz"
        field.configuration_model = "foobarbaz"
        field.boost = 89.98
        result = field.generate_search_fields(model)
        mock_field.assert_called_once_with(
            "arg",
            "arg2",
            model_field_name="bar",
            boost=89.98,
            parent_field="baz",
            configuration_model="foobarbaz",
            kwarg="value",
        )

        mock_field.reset_mock()
        field.search_kwargs = {"another": 33, "yet_another": True}
        result = field.generate_search_fields(model)
        mock_field.assert_called_once_with(
            "arg",
            "arg2",
            model_field_name="bar",
            boost=89.98,
            parent_field="baz",
            configuration_model="foobarbaz",
            kwarg="value",
            another=33,
            yet_another=True,
        )

    def test_generate_autocomplete_fields(self, mocker):
        mock_get_variants = mocker.patch(
            "extended_search.index.IndexedField.get_autocomplete_field_variants",
            return_value=[],
        )
        mock_field = mocker.patch("extended_search.index.AutocompleteField")
        model = mocker.Mock()
        field = IndexedField("foo", model_field_name="bar")

        assert field.generate_autocomplete_fields(model) == []

        mock_get_variants.return_value = [
            (("arg", "arg2"), {"kwarg": "value"}),
        ]
        result = field.generate_autocomplete_fields(model)
        assert len(result) == 1
        assert isinstance(result[0], mocker.MagicMock)
        mock_field.assert_called_once_with(
            "arg",
            "arg2",
            model_field_name="bar",
            parent_field=None,
            configuration_model=None,
            kwarg="value",
        )

        mock_field.reset_mock()
        field.parent_field = "baz"
        field.configuration_model = "foobarbaz"
        result = field.generate_autocomplete_fields(model)
        mock_field.assert_called_once_with(
            "arg",
            "arg2",
            model_field_name="bar",
            parent_field="baz",
            configuration_model="foobarbaz",
            kwarg="value",
        )

        mock_field.reset_mock()
        field.autocomplete_kwargs = {"another": 33, "yet_another": True}
        result = field.generate_autocomplete_fields(model)
        mock_field.assert_called_once_with(
            "arg",
            "arg2",
            model_field_name="bar",
            parent_field="baz",
            configuration_model="foobarbaz",
            kwarg="value",
            another=33,
            yet_another=True,
        )

    def test_generate_filter_fields(self, mocker):
        mock_get_variants = mocker.patch(
            "extended_search.index.IndexedField.get_filter_field_variants",
            return_value=[],
        )
        mock_field = mocker.patch("extended_search.index.FilterField")
        model = mocker.Mock()
        field = IndexedField("foo", model_field_name="bar")
        assert field.generate_filter_fields(model) == []
        mock_get_variants.return_value = [
            (("arg", "arg2"), {"kwarg": "value"}),
        ]
        result = field.generate_filter_fields(model)
        assert len(result) == 1
        assert isinstance(result[0], mocker.MagicMock)
        mock_field.assert_called_once_with(
            "arg",
            "arg2",
            model_field_name="bar",
            parent_field=None,
            configuration_model=None,
            kwarg="value",
        )

        mock_field.reset_mock()
        field.parent_field = "baz"
        field.configuration_model = "foobarbaz"
        result = field.generate_filter_fields(model)
        mock_field.assert_called_once_with(
            "arg",
            "arg2",
            model_field_name="bar",
            parent_field="baz",
            configuration_model="foobarbaz",
            kwarg="value",
        )

        mock_field.reset_mock()
        field.filter_kwargs = {"another": 33, "yet_another": True}
        result = field.generate_filter_fields(model)
        mock_field.assert_called_once_with(
            "arg",
            "arg2",
            model_field_name="bar",
            parent_field="baz",
            configuration_model="foobarbaz",
            kwarg="value",
            another=33,
            yet_another=True,
        )

    def test_get_search_field_variants(self, mocker):
        model = mocker.Mock()
        field = IndexedField("foo", model_field_name="bar", search=False)
        assert field.get_search_field_variants(model) == []
        field.search = True
        assert field.get_search_field_variants(model) == [(("bar",), {})]

    def test_get_autocomplete_field_variants(self, mocker):
        model = mocker.Mock()
        field = IndexedField("foo", model_field_name="bar", autocomplete=False)
        assert field.get_autocomplete_field_variants(model) == []
        field.autocomplete = True
        assert field.get_autocomplete_field_variants(model) == [(("bar",), {})]

    def test_get_filter_field_variants(self, mocker):
        model = mocker.Mock()
        field = IndexedField("foo", model_field_name="bar", filter=False)
        assert field.get_filter_field_variants(model) == []
        field.filter = True
        assert field.get_filter_field_variants(model) == [(("bar",), {})]


class TestMultiQueryIndexedField:
    def test_init_params_accepted_defaults_and_all_saved(self):
        field = MultiQueryIndexedField("foo")
        assert field.field_name == "foo"
        assert field.model_field_name == field.field_name
        assert field.boost == 1.0
        assert not field.search
        assert not field.autocomplete
        assert not field.filter
        assert not field.fuzzy
        assert not field.tokenized
        assert not field.explicit

        field = MultiQueryIndexedField(
            "foo",
            explicit=True,
            tokenized=True,
            fuzzy=True,
        )
        assert field.search
        assert not field.autocomplete
        assert not field.filter
        assert field.explicit
        assert field.tokenized
        assert field.fuzzy

    def test_init_params_set_search_param_when_needed(self):
        field = MultiQueryIndexedField("foo", tokenized=True)
        assert field.search
        assert not field.autocomplete
        assert not field.filter
        assert not field.explicit
        assert field.tokenized
        assert not field.fuzzy

        field = MultiQueryIndexedField("foo", explicit=True)
        assert field.search
        assert not field.autocomplete
        assert not field.filter
        assert field.explicit
        assert not field.tokenized
        assert not field.fuzzy

        field = MultiQueryIndexedField("foo", fuzzy=True)
        assert field.search
        assert not field.autocomplete
        assert not field.filter
        assert not field.explicit
        assert not field.tokenized
        assert field.fuzzy

    def test_get_search_analyzers(self):
        field = MultiQueryIndexedField("foo")
        assert field.get_search_analyzers() == set()
        field = MultiQueryIndexedField("foo", tokenized=True)
        assert field.get_search_analyzers() == {AnalysisType.TOKENIZED}
        field = MultiQueryIndexedField("foo", explicit=True)
        assert field.get_search_analyzers() == {AnalysisType.EXPLICIT}
        field = MultiQueryIndexedField("foo", search=True)
        assert field.get_search_analyzers() == {AnalysisType.TOKENIZED}
        field = MultiQueryIndexedField("foo", search=True, explicit=True)
        assert field.get_search_analyzers() == {AnalysisType.EXPLICIT}
        field = MultiQueryIndexedField("foo", search=True, tokenized=True)
        assert field.get_search_analyzers() == {AnalysisType.TOKENIZED}
        field = MultiQueryIndexedField("foo", explicit=True, tokenized=True)
        assert field.get_search_analyzers() == {
            AnalysisType.EXPLICIT,
            AnalysisType.TOKENIZED,
        }

    def test_get_autocomplete_analyzers(self):
        field = MultiQueryIndexedField("foo", autocomplete=False)
        assert field.get_autocomplete_analyzers() == set()
        field.autocomplete = True
        assert field.get_autocomplete_analyzers() == {AnalysisType.NGRAM}

    def test_get_filter_analyzers(self):
        field = MultiQueryIndexedField("foo", filter=False)
        assert field.get_filter_analyzers() == set()
        field.filter = True
        assert field.get_filter_analyzers() == {AnalysisType.FILTER}

    def test_get_search_field_variants(self, mocker):
        mock_get_name = mocker.patch(
            "extended_search.index.get_indexed_field_name",
            return_value="--field-name--",
        )
        mock_analyzers = mocker.patch(
            "extended_search.index.MultiQueryIndexedField.get_search_analyzers",
            return_value=[],
        )

        model = mocker.Mock()
        field = MultiQueryIndexedField("foo")
        assert field.get_search_field_variants(model) == []
        mock_analyzers.assert_called_once_with()
        mock_get_name.assert_not_called()

        mock_analyzers.reset_mock()
        mock_analyzers.return_value = [AnalysisType.TOKENIZED]
        assert field.get_search_field_variants(model) == [
            (
                ("--field-name--",),
                {
                    "es_extra": {
                        "analyzer": settings.extended_search_settings["analyzers"][
                            AnalysisType.TOKENIZED.value
                        ]["es_analyzer"]
                    }
                },
            )
        ]
        mock_analyzers.assert_called_once_with()
        mock_get_name.assert_called_once_with("foo", AnalysisType.TOKENIZED)

        mock_analyzers.reset_mock()
        mock_get_name.reset_mock()
        mock_analyzers.return_value = [AnalysisType.EXPLICIT, AnalysisType.TOKENIZED]
        assert field.get_search_field_variants(model) == [
            (
                ("--field-name--",),
                {
                    "es_extra": {
                        "analyzer": settings.extended_search_settings["analyzers"][
                            AnalysisType.EXPLICIT.value
                        ]["es_analyzer"]
                    }
                },
            ),
            (
                ("--field-name--",),
                {
                    "es_extra": {
                        "analyzer": settings.extended_search_settings["analyzers"][
                            AnalysisType.TOKENIZED.value
                        ]["es_analyzer"]
                    }
                },
            ),
        ]


class TestDWIndexedField:
    def test_init_params_accepted_defaults_and_all_saved(self):
        field = DWIndexedField("foo")
        assert field.field_name == "foo"
        assert field.model_field_name == field.field_name
        assert field.boost == 1.0
        assert not field.search
        assert not field.autocomplete
        assert not field.filter
        assert not field.fuzzy
        assert not field.tokenized
        assert not field.explicit
        assert not field.keyword

    def test_init_params_set_search_param_when_needed(self):
        field = DWIndexedField("foo", keyword=True)
        assert field.search
        assert not field.autocomplete
        assert not field.filter
        assert not field.explicit
        assert not field.tokenized
        assert field.keyword
        assert not field.fuzzy

    def test_get_search_analyzers(self, mocker):
        mocker.patch(
            "extended_search.index.MultiQueryIndexedField.get_search_analyzers",
            return_value=set(),
        )
        field = DWIndexedField("foo", keyword=False)
        assert field.get_search_analyzers() == set()
        field.keyword = True
        assert field.get_search_analyzers() == {AnalysisType.KEYWORD}


class TestGetIndexedField:
    @pytest.mark.django_db
    def test_get_indexed_field_name(self):
        with pytest.raises(AttributeError):
            get_indexed_field_name("foo", "bar")
        analyzer = AnalysisType.TOKENIZED
        assert get_indexed_field_name("foo", analyzer) == "foo"

        settings.settings_singleton["analyzers"][analyzer.value][
            "index_fieldname_suffix"
        ] = "bar"
        settings.extended_search_settings = settings.settings_singleton.to_dict()

        assert (
            settings.settings_singleton["analyzers"][analyzer.value][
                "index_fieldname_suffix"
            ]
            == "bar"
        )
        assert get_indexed_field_name("foo", analyzer) == "foobar"

        settings.settings_singleton["analyzers"][analyzer.value][
            "index_fieldname_suffix"
        ] = ""
        settings.extended_search_settings = settings.settings_singleton.to_dict()
