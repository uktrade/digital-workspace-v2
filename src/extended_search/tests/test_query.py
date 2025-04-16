import pytest
from wagtail.search.query import PlainText

from extended_search.query import Filtered, Nested, OnlyFields


class TestOnlyFields:
    def test_init_sets_attributes(self):
        with pytest.raises(TypeError, match=r".* missing 3 required positional .*"):
            of = OnlyFields()
        with pytest.raises(TypeError, match=r".* missing 2 required positional .*"):
            of = OnlyFields("foo")
        with pytest.raises(TypeError, match=r".* missing 1 required positional .*"):
            of = OnlyFields("foo", only_model="fuzz")
        with pytest.raises(
            TypeError, match="The `subquery` parameter must be of type SearchQuery"
        ):
            of = OnlyFields("foo", "bar", only_model="fuzz")
        with pytest.raises(TypeError, match="The `fields` parameter must be a list"):
            of = OnlyFields(PlainText("foo"), "bar", only_model="fuzz")

        of = OnlyFields(
            PlainText("foo"),
            [
                "bar",
            ],
            only_model="fuzz",
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
                    only_model="fuzz",
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
                    only_model="fuzz",
                )
            )
            == f"<OnlyFields {repr(PlainText('foo'))} fields=['bar', 'baz']>"
        )


class TestNested:
    def test_init_sets_attributes(self):
        with pytest.raises(TypeError, match=r".* missing 2 required positional .*"):
            te = Nested()
        with pytest.raises(TypeError, match=r".* missing 1 required positional .*"):
            te = Nested("foo")
        with pytest.raises(
            TypeError, match="The `subquery` parameter must be of type SearchQuery"
        ):
            te = Nested("foo", "bar")
        with pytest.raises(TypeError, match="The `path` parameter must be a string"):
            te = Nested(PlainText("foo"), ["bar"])

        te = Nested(
            PlainText("foo"),
            "bar",
        )

        assert repr(te.subquery) == repr(PlainText("foo"))
        assert te.path == "bar"

    def test_repr(self):
        assert (
            repr(
                Nested(
                    PlainText("foo"),
                    "bar",
                )
            )
            == f"<Nested {repr(PlainText('foo'))} path='bar'>"
        )


class TestFiltered:
    def test_init_sets_attributes(self):
        with pytest.raises(TypeError, match=r".* missing 2 required positional .*"):
            fi = Filtered()
        with pytest.raises(TypeError, match=r".* missing 1 required positional .*"):
            fi = Filtered("foo")
        with pytest.raises(
            TypeError, match="The `subquery` parameter must be of type SearchQuery"
        ):
            fi = Filtered("foo", "bar")
        with pytest.raises(
            TypeError, match="The `filters` parameter must be a list of thruples"
        ):
            fi = Filtered(PlainText("foo"), "bar")
        with pytest.raises(
            TypeError, match="The `filters` parameter must be a list of thruples"
        ):
            fi = Filtered(PlainText("foo"), ["bar"])
        with pytest.raises(
            TypeError, match="The `filters` parameter must be a list of thruples"
        ):
            fi = Filtered(PlainText("foo"), [("bar",)])

        fi = Filtered(
            PlainText("foo"),
            [
                ("bar", "baz", "foobar"),
            ],
        )

        assert repr(fi.subquery) == repr(PlainText("foo"))
        assert fi.filters == [
            ("bar", "baz", "foobar"),
        ]

    def test_repr(self):
        assert (
            repr(
                Filtered(
                    PlainText("foo"),
                    [
                        ("bar", "baz", "foobar"),
                    ],
                )
            )
            == f"<Filtered {repr(PlainText('foo'))} filters=[('bar', 'baz', 'foobar')]>"
        )
        assert (
            repr(
                Filtered(
                    PlainText("foo"),
                    [
                        ("bar", "baz", "foobar"),
                    ],
                )
            )
            == f"<Filtered {repr(PlainText('foo'))} filters=[('bar', 'baz', 'foobar')]>"
        )
