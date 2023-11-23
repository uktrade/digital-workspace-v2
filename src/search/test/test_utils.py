import doctest

from django.test import override_settings

import search
from search.utils import get_bad_score_threshold, has_only_bad_results


def test_doctests():
    results = doctest.testmod(search.utils)
    assert results.failed == 0


class TestBadScoreThreshold:
    def test_default(self, mocker):
        category = "test_category"
        mock_get_all_subqueries = mocker.patch(
            "search.utils.get_all_subqueries",
            return_value={
                category: [
                    {
                        "boost": 610,
                    },
                    {
                        "boost": 52,
                    },
                    {
                        "boost": 4,
                    },
                ],
            },
        )
        query = "test query"

        output = get_bad_score_threshold(query, category)

        assert output == 222
        mock_get_all_subqueries.assert_called_once_with(query)

    @override_settings(BAD_SEARCH_SCORE_MULTIPLIERS={"test_category": 2})
    def test_with_settings(self, mocker):
        category = "test_category"
        mock_get_all_subqueries = mocker.patch(
            "search.utils.get_all_subqueries",
            return_value={
                category: [
                    {
                        "boost": 610,
                    },
                    {
                        "boost": 52,
                    },
                    {
                        "boost": 4,
                    },
                ],
            },
        )
        query = "test query"

        output = get_bad_score_threshold(query, category)

        assert output == 444
        mock_get_all_subqueries.assert_called_once_with(query)


class TestHasOnlyBadResults:
    def test_has_pinned_results(self, mocker):
        mock_result = mocker.Mock()
        mock_result._score = 10

        query = "test query"
        category = "test_category"
        pinned_results = [mock_result]
        search_results = [mock_result]

        output = has_only_bad_results(query, category, pinned_results, search_results)

        assert output is False

    def test_without_search_results(self, mocker):
        mock_result = mocker.Mock()
        mock_result._score = 10

        query = "test query"
        category = "test_category"
        pinned_results = []
        search_results = []

        output = has_only_bad_results(query, category, pinned_results, search_results)

        assert output is False

    def test_highest_score_above_threshold(self, mocker):
        mock_get_bad_score_threshold = mocker.patch(
            "search.utils.get_bad_score_threshold", return_value=9
        )
        mock_result = mocker.Mock()
        mock_result._score = 10

        query = "test query"
        category = "test_category"
        pinned_results = []
        search_results = [mock_result]

        output = has_only_bad_results(query, category, pinned_results, search_results)

        assert output is False
        mock_get_bad_score_threshold.assert_called_once_with(query, category)

    def test_highest_score_below_threshold(self, mocker):
        mock_get_bad_score_threshold = mocker.patch(
            "search.utils.get_bad_score_threshold", return_value=11
        )
        mock_result = mocker.Mock()
        mock_result._score = 10

        query = "test query"
        category = "test_category"
        pinned_results = []
        search_results = [mock_result]

        output = has_only_bad_results(query, category, pinned_results, search_results)

        assert output is True
        mock_get_bad_score_threshold.assert_called_once_with(query, category)

    def test_highest_score_equals_threshold(self, mocker):
        mock_get_bad_score_threshold = mocker.patch(
            "search.utils.get_bad_score_threshold", return_value=10
        )
        mock_result = mocker.Mock()
        mock_result._score = 10

        query = "test query"
        category = "test_category"
        pinned_results = []
        search_results = [mock_result]

        output = has_only_bad_results(query, category, pinned_results, search_results)

        assert output is True
        mock_get_bad_score_threshold.assert_called_once_with(query, category)
