import pytest

from extended_search.settings import (
    extended_search_settings,
    DEFAULT_SETTINGS,
    Settings,
)


pytestmark = pytest.mark.xfail


class TestDefaults:
    def test_required_keys_set(self):
        ...


class TestSettings:
    def test_get_from_env_retrieves_env_var(self):
        ...

    def test_get_from_django_settings_retrieves_setting(self):
        ...

    def test_get_from_defaults_retrieves_default(self):
        ...

    def test_get_from_admin_retrieves_admin_setting(self):
        ...

    def test_getter_adheres_to_setting_hierarchy(self):
        ...

    def test_getter_uses_all_submethods(self):
        ...

    def test_get_boost_value_uses_getter(self):
        ...

    def test_get_boost_value_retrieves_val_from_key(self):
        ...
