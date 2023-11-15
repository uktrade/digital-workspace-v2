import pytest

from extended_search.managers import get_indexed_field_name
from extended_search.models import Setting
from extended_search.settings import extended_search_settings
from extended_search.types import AnalysisType


class TestManagersInit:
    @pytest.mark.django_db
    def test_get_indexed_field_name(self):
        with pytest.raises(AttributeError):
            get_indexed_field_name("foo", "bar")
        analyzer = AnalysisType.TOKENIZED
        assert get_indexed_field_name("foo", analyzer) == "foo"

        Setting.objects.create(
            key=f"analyzers__{analyzer.value}__index_fieldname_suffix", value="bar"
        )
        assert (
            extended_search_settings[
                f"analyzers__{analyzer.value}__index_fieldname_suffix"
            ]
            == "bar"
        )
        assert get_indexed_field_name("foo", analyzer) == "foobar"
