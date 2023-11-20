import pytest

from extended_search import managers
from extended_search.models import Setting
from extended_search import settings
from extended_search.types import AnalysisType
from extended_search import signals


class TestManagersInit:
    @pytest.mark.django_db
    @pytest.mark.xfail
    def test_get_indexed_field_name(self):
        with pytest.raises(AttributeError):
            managers.get_indexed_field_name("foo", "bar")
        analyzer = AnalysisType.TOKENIZED
        assert managers.get_indexed_field_name("foo", analyzer) == "foo"
        assert settings.extended_search_settings == managers.extended_search_settings

        Setting.objects.create(
            key=f"analyzers__{analyzer.value}__index_fieldname_suffix", value="bar"
        )

        # signals.update_searchsetting_queryset("")

        assert (
            settings.settings_singleton["analyzers"][analyzer.value][
                "index_fieldname_suffix"
            ]
            == "bar"
        )
        assert (
            settings.extended_search_settings["analyzers"][analyzer.value][
                "index_fieldname_suffix"
            ]
            == "bar"
        )

        assert (
            managers.extended_search_settings["analyzers"][analyzer.value][
                "index_fieldname_suffix"
            ]
            == "bar"
        )
        assert managers.get_indexed_field_name("foo", analyzer) == "foobar"
