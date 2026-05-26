import unittest

# from datetime import datetime
from unittest.mock import AsyncMock, patch

from src.core import AsyncClientBundle
from src.reddit import SortOption, StreamBuilder


class TestConstructor(unittest.TestCase):

    def test_default_args(self):
        mock_client = AsyncMock()
        bundle = AsyncClientBundle(http_client=mock_client)
        builder = StreamBuilder()
        stream = builder.build(bundle)
        # TODO

        expected = []

        for item in zip(stream, expected, strict=True):
            self.assertEqual(item, expected)

    def test_specified_args(self):
        mock_client = AsyncMock()
        bundle = AsyncClientBundle(http_client=mock_client)
        builder = StreamBuilder(
            SortOption.TOP_ALL,
        )
        stream = builder.build(bundle)

        expected = []

        for item in zip(stream, expected, strict=True):
            self.assertEqual(item, expected)


class TestAddSubreddit(unittest.TestCase):

    @patch("asyncpraw.Reddit.subreddit")
    def test_with_rslash_prefix(self):
        mock_client = AsyncMock()
        bundle = AsyncClientBundle(http_client=mock_client)
        builder = StreamBuilder()
        builder.add_subreddit("r/wallpapers")
        stream = builder.build(bundle)

        expected = []

        for item in zip(stream, expected, strict=True):
            self.assertEqual(item, expected)

        # @patch("asyncpraw.Reddit.subreddit")

    @patch("asyncpraw.Reddit.subreddit")
    def test_without_rslash_prefix(self):
        mock_client = AsyncMock()
        bundle = AsyncClientBundle(http_client=mock_client)
        builder = StreamBuilder()
        builder.add_subreddit("wallpapers")
        stream = builder.build(bundle)
        # TODO

        expected = []

        for item in zip(stream, expected, strict=True):
            self.assertEqual(item, expected)

        # @patch("asyncpraw.Reddit.subreddit")


class TestSetRedditor(unittest.TestCase):
    """
    reddit_sentinel = object()

    def test_creates_and_returns_reddit_object(self, monkeypatch):
        monkeypatch.setenv("REDDIT_CLIENT_ID", "mock reddit client id")
        monkeypatch.setenv("REDDIT_CLIENT_SECRET", "mock reddit client secret")
        monkeypatch.setenv("IMGUR_CLIENT_ID", "mock imgur client id")
        monkeypatch.setenv("IMGUR_CLIENT_SECRET", "mock imgur client secret")

        client_bundle = AsyncClientBundle()
        assert client_bundle.reddit is None

        with patch.object(
            asyncpraw.Reddit, "__new__", return_value=self.reddit_sentinel
        ) as mock_reddit:
            reddit = client_bundle.set_reddit()
            mock_reddit.assert_called_once()
            assert reddit == self.reddit_sentinel
            assert client_bundle.reddit == self.reddit_sentinel
    """

    @patch("asyncpraw.Reddit.subreddit")
    @patch("asyncpraw.Reddit.redditor")
    def changes_redditor(self):
        builder = StreamBuilder()
        builder.set_redditor("mock username", "mock password")
        self.assertEqual(builder.redditor[0], "mock username")
        self.assertEqual(builder.redditor[1], "mock password")
        stream = builder.build()
        # TODO

        expected = []

        for item in zip(stream, expected, strict=True):
            self.assertEqual(item, expected)


class TestDefaultSortby(unittest.TestCase):

    def test_changes_sortby(self):
        mock_client = AsyncMock()
        bundle = AsyncClientBundle(http_client=mock_client)
        builder = StreamBuilder()
        builder.set_default_sortby(SortOption.TOP_ALL)
        self.assertEqual(builder.sortby, SortOption.TOP_ALL)
        stream = builder.build(bundle)
        # TODO

        expected = []

        for item in zip(stream, expected, strict=True):
            self.assertEqual(item, expected)
