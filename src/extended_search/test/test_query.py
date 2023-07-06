import pytest

from extended_search.backends.query import OnlyFields
from wagtail.search.query import PlainText


class TestOnlyFields:
    def test_init_sets_attributes(self):
        with pytest.raises(TypeError, match=r".* missing 2 required positional .*"):
            of = OnlyFields()
        with pytest.raises(TypeError, match=r".* missing 1 required positional .*"):
            of = OnlyFields("foo")
        with pytest.raises(
            TypeError, match="The `subquery` parameter must be of type SearchQuery"
        ):
            of = OnlyFields("foo", "bar")
        with pytest.raises(TypeError, match="The `fields` parameter must be a list"):
            of = OnlyFields(PlainText("foo"), "bar")

        of = OnlyFields(
            PlainText("foo"),
            [
                "bar",
            ],
        )

        assert repr(of.subquery) == repr(PlainText("foo"))
        assert of.fields == [
            "bar",
        ]

    def test_repr(self):
        assert (
            repr(
                OnlyFields(
                    PlainText("foo"),
                    [
                        "bar",
                    ],
                )
            )
            == f"<OnlyFields {repr(PlainText('foo'))} fields=['bar']>"
        )
        assert (
            repr(
                OnlyFields(
                    PlainText("foo"),
                    [
                        "bar",
                        "baz",
                    ],
                )
            )
            == f"<OnlyFields {repr(PlainText('foo'))} fields=['bar', 'baz']>"
        )
