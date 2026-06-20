import unittest
from collections import Counter
from unittest.mock import MagicMock, patch

from src.core import AsyncClientBundle
from src.reddit import SortOption, StreamBuilder, SubmissionWrapper
from tests import SubmissionMockFactory, acollect, async_iter


class TestConstructor(unittest.IsolatedAsyncioTestCase):

    async def test_empty_builder_yields_nothing(self):
        # no subreddits and no redditor -> the merged stream is empty (and must
        # terminate, which exercises merge()'s zero-generator path)
        async with AsyncClientBundle() as clients:
            with patch.object(clients, "set_reddit", return_value=MagicMock()):
                stream = StreamBuilder().build(clients)
                self.assertEqual(await acollect(stream), [])


class TestAddSubreddit(unittest.IsolatedAsyncioTestCase):

    async def _build_and_collect(self, name):
        mock_reddit = MagicMock()
        mock_reddit.subreddit.return_value = MagicMock()

        async with AsyncClientBundle() as clients:
            with patch.object(clients, "set_reddit", return_value=mock_reddit):
                # inject a fake sort option so we don't touch asyncpraw internals
                builder = StreamBuilder(sortby=lambda sub: async_iter([]))
                builder.add_subreddit(name)
                result = await acollect(builder.build(clients))
        return mock_reddit, result

    async def test_with_rslash_prefix(self):
        mock_reddit, result = await self._build_and_collect("r/wallpapers")
        mock_reddit.subreddit.assert_called_once_with("wallpapers")
        self.assertEqual(result, [])

    async def test_without_rslash_prefix(self):
        mock_reddit, result = await self._build_and_collect("wallpapers")
        mock_reddit.subreddit.assert_called_once_with("wallpapers")
        self.assertEqual(result, [])

    async def test_wraps_and_filters_submissions(self):
        sub_a = SubmissionMockFactory(over_18=False)
        sub_b = SubmissionMockFactory(over_18=True)

        mock_reddit = MagicMock()
        mock_reddit.subreddit.return_value = MagicMock()

        async with AsyncClientBundle() as clients:
            with patch.object(clients, "set_reddit", return_value=mock_reddit):
                builder = StreamBuilder(
                    sortby=lambda sub: async_iter([sub_a, sub_b]),
                    predicate=lambda w: not w.nsfw,  # drop NSFW posts
                )
                builder.add_subreddit("wallpapers")
                result = await acollect(builder.build(clients))

        # sub_b (NSFW) is filtered out; sub_a is wrapped into a SubmissionWrapper
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], SubmissionWrapper)
        self.assertEqual(result[0].title, sub_a.title)


class TestSetRedditor(unittest.IsolatedAsyncioTestCase):

    async def test_changes_redditor(self):
        builder = StreamBuilder()
        builder.set_redditor("mock username", "mock password")
        self.assertEqual(builder.redditor[0], "mock username")
        self.assertEqual(builder.redditor[1], "mock password")

    async def test_redditor_stream(self):
        saved = SubmissionMockFactory()
        mock_reddit = MagicMock()
        # build() appends reddit.redditor(name) directly as a stream
        mock_reddit.redditor.return_value = async_iter([saved])

        async with AsyncClientBundle() as clients:
            with patch.object(clients, "set_reddit", return_value=mock_reddit):
                builder = StreamBuilder()
                builder.set_redditor("user", "pw")
                result = await acollect(builder.build(clients))

        mock_reddit.redditor.assert_called_once_with("user")
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], SubmissionWrapper)
        self.assertEqual(result[0].title, saved.title)


class TestMultiSource(unittest.IsolatedAsyncioTestCase):

    async def test_merges_subreddit_and_redditor(self):
        saved = SubmissionMockFactory()
        sub_a = SubmissionMockFactory()
        sub_b = SubmissionMockFactory()

        mock_reddit = MagicMock()
        mock_reddit.redditor.return_value = async_iter([saved])
        mock_reddit.subreddit.return_value = MagicMock()

        async with AsyncClientBundle() as clients:
            with patch.object(clients, "set_reddit", return_value=mock_reddit):
                builder = StreamBuilder(sortby=lambda sub: async_iter([sub_a, sub_b]))
                builder.set_redditor("user", "pw")
                builder.add_subreddit("wallpapers")
                result = await acollect(builder.build(clients))

        # order is non-deterministic (merge) -> compare titles as a multiset
        self.assertEqual(
            Counter(w.title for w in result),
            Counter([saved.title, sub_a.title, sub_b.title]),
        )


class TestDefaultSortby(unittest.IsolatedAsyncioTestCase):

    async def test_changes_sortby(self):
        builder = StreamBuilder()
        builder.set_default_sortby(SortOption.TOP_ALL)
        self.assertEqual(builder.sortby, SortOption.TOP_ALL)
