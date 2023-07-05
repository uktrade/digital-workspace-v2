import pytest

from extended_search.fields import (
    AbstractBaseField,
    BaseIndexedField,
    IndexedField,
    RelatedIndexedFields,
)


pytestmark = pytest.mark.xfail


class TestAbstractBaseField:
    def test_init_params_all_saved_as_kwargs(self):
        ...

    def test_init_params_accepted(self):
        ...

    def test_init_model_field_name_defaults_to_name(self):
        ...

    def test_init_boost_defaults_to_1_0(self):
        ...

    def test_get_base_mapping_object_format(self):
        ...

    def test_get_mapping_uses_get_base_mapping_object(self):
        ...

    def test_mapping_property_uses_get_mapping_method(self):
        ...


class TestBaseIndexedField:
    def test_init_params_all_saved_as_kwargs(self):
        ...

    def test_init_params_accepted(self):
        ...

    def test_init_fuzzy_param_sets_search_param(self):
        ...

    def test_get_search_mapping_object_format(self):
        ...

    def test_get_autocomplete_mapping_object_format(self):
        ...

    def test_get_filter_mapping_object_format(self):
        ...

    def test_get_mapping_uses_sub_methods(self):
        ...


class TestIndexedField:
    def test_init_params_all_saved_as_kwargs(self):
        ...

    def test_init_params_accepted(self):
        ...

    def test_init_params_set_search_param_when_needed(self):
        ...

    def test_get_search_mapping_object_format(self):
        ...

    def test_get_search_mapping_object_uses_parent_method(self):
        ...


class TestRelatedIndexedFields:
    def test_init_params_all_saved_as_kwargs(self):
        ...

    def test_init_params_accepted(self):
        ...

    def test_get_related_mapping_object_format(self):
        ...

    def test_get_mapping_uses_sub_methods(self):
        ...


# @pytest.mark.parametrize(
#     "query,result",
#     [
#         ("Gôod morninç øæå", "Good morninc a"),
#         (
#             "Mieux vaut être seul que mal accompagné",
#             "Mieux vaut etre seul que mal accompagne",
#         ),
#         ("Après la pluie, le beau temps", "Apres la pluie le beau temps"),
#         ("À bon chat, bon rat", "A bon chat bon rat"),
#         ("Lăpușneanu", "Lapusneanu"),
#         ("Пожалуйста", ""),
#         # ensure composite chars are also folded
#         ("Ç is the same as \u0043\u0327", "C is the same as C"),
#     ],
# )
# def test_sanitize_asciifolds_accented_chars(query, result):
#     assert sanitize_search_query(query) == result


# from django.test import Client, TestCase

# from peoplefinder.services.person import PersonService
# from user.test.factories import UserFactory


# class TestSearchView(TestCase):
#     def test_empty_query(self):
#         user = UserFactory()
#         PersonService().create_user_profile(user)
#         c = Client()

#         c.force_login(user)
#         response = c.get("/search/", {"query": ""}, follow=True)

#         self.assertEqual(response.status_code, 200)
