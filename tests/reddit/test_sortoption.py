import unittest
from unittest.mock import create_autospec

from asyncpraw.models import Subreddit

from src.reddit import SortOption

# every option and the asyncpraw call it should make
EXPECTED_CALLS = {
    SortOption.NEW: ("new", {}),
    SortOption.HOT: ("hot", {}),
    SortOption.CONTROVERSIAL: ("controversial", {}),
    SortOption.TOP_ALL: ("top", {"time_filter": "all"}),
    SortOption.TOP_DAY: ("top", {"time_filter": "day"}),
    SortOption.TOP_HOUR: ("top", {"time_filter": "hour"}),
    SortOption.TOP_WEEK: ("top", {"time_filter": "week"}),
    SortOption.TOP_MONTH: ("top", {"time_filter": "month"}),
    SortOption.TOP_YEAR: ("top", {"time_filter": "year"}),
}


class TestSortOption(unittest.TestCase):

    def test_every_option_is_a_member(self):
        # a bare partial isn't an enum member on modern Python; without member()
        # options silently disappear from the enum (and from --sortby)
        self.assertEqual(set(SortOption), set(EXPECTED_CALLS))

    def test_each_option_calls_a_real_listing_method(self):
        for option, (method, kwargs) in EXPECTED_CALLS.items():
            with self.subTest(option.name):
                # autospec rejects methods asyncpraw's Subreddit doesn't have
                # (a plain MagicMock accepted the removed gilded()) and
                # arguments it wouldn't accept
                subreddit = create_autospec(Subreddit, instance=True)
                result = option(subreddit, limit=5)
                getattr(subreddit, method).assert_called_once_with(**kwargs, limit=5)
                self.assertIs(result, getattr(subreddit, method).return_value)
