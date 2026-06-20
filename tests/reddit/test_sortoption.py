import unittest
from unittest.mock import MagicMock

from src.reddit import SortOption


class TestSortOptionMembers(unittest.TestCase):

    def test_all_options_are_members(self):
        names = {o.name for o in SortOption}
        expected = {
            "NEW",
            "HOT",
            "CONTROVERSIAL",
            "GILDED",
            "TOP_ALL",
            "TOP_DAY",
            "TOP_HOUR",
            "TOP_WEEK",
            "TOP_MONTH",
            "TOP_YEAR",
        }
        self.assertEqual(names, expected)

    def test_lookup_by_name(self):
        self.assertIs(SortOption["HOT"], SortOption.HOT)

    def test_hot_calls_subreddit_hot(self):
        sub = MagicMock()
        SortOption.HOT(sub)
        sub.hot.assert_called_once_with()

    def test_new_calls_subreddit_new(self):
        sub = MagicMock()
        SortOption.NEW(sub)
        sub.new.assert_called_once_with()

    def test_top_all_passes_time_filter(self):
        sub = MagicMock()
        SortOption.TOP_ALL(sub)
        sub.top.assert_called_once_with(time_filter="all")

    def test_top_day_passes_time_filter(self):
        sub = MagicMock()
        SortOption.TOP_DAY(sub)
        sub.top.assert_called_once_with(time_filter="day")

    def test_call_returns_value(self):
        sub = MagicMock()
        sub.hot.return_value = "sentinel"
        self.assertEqual(SortOption.HOT(sub), "sentinel")
