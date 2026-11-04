import json
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from tests import SubmissionWrapperFactory


class TestLogRecord(unittest.TestCase):

    def test_builds_record(self):
        wrapper = SubmissionWrapperFactory()
        wrapper._submission.id = "abc123"
        wrapper.urls = ["https://imgur.com/2", "https://imgur.com/1"]

        record = wrapper.log_record()

        self.assertEqual(record["id"], "abc123")
        self.assertEqual(record["url"], wrapper._submission.url)
        self.assertEqual(record["exception"], "")
        # in discovery order, and JSON-serializable
        self.assertEqual(
            record["recognized_urls"],
            ["https://imgur.com/2", "https://imgur.com/1"],
        )
        json.dumps(record)

    def test_record_with_exception(self):
        wrapper = SubmissionWrapperFactory()
        wrapper._submission.id = "xyz"
        record = wrapper.log_record(exception="boom")
        self.assertEqual(record["exception"], "boom")
        self.assertEqual(record["recognized_urls"], [])


class TestFindUrls(unittest.IsolatedAsyncioTestCase):

    async def test_find_urls_sets_urls_and_awaits_parser(self):
        wrapper = SubmissionWrapperFactory(url="https://example.com/post")
        mock_clients = MagicMock()

        with patch(
            "src.reddit.submission_wrapper.parse_find_urls",
            new_callable=AsyncMock,
        ) as mock_find:
            mock_find.return_value = ["https://img/1", "https://img/2"]
            result = await wrapper.find_urls(mock_clients)

        mock_find.assert_awaited_once_with("https://example.com/post", mock_clients)
        self.assertEqual(wrapper.urls, ["https://img/1", "https://img/2"])
        self.assertEqual(result, ["https://img/1", "https://img/2"])
        self.assertTrue(wrapper.has_urls())

    async def test_find_urls_empty(self):
        wrapper = SubmissionWrapperFactory(url="https://example.com/post")
        mock_clients = MagicMock()

        with patch(
            "src.reddit.submission_wrapper.parse_find_urls",
            new_callable=AsyncMock,
        ) as mock_find:
            mock_find.return_value = []
            await wrapper.find_urls(mock_clients)

        self.assertEqual(wrapper.urls, [])
        self.assertFalse(wrapper.has_urls())


class TestFindUrlsUsesListingData(unittest.IsolatedAsyncioTestCase):
    """
    Reddit-hosted media comes with the listing, so it shouldn't cost a parser
    run (an extra reddit API call for galleries)
    """

    async def _find(self, submission):
        wrapper = SubmissionWrapperFactory(submission=submission)
        with patch(
            "src.reddit.submission_wrapper.parse_find_urls",
            new_callable=AsyncMock,
            return_value=["https://parsed/1"],
        ) as mock_find:
            result = await wrapper.find_urls(MagicMock())
        return result, mock_find

    @staticmethod
    def _submission(**fields):
        base = {
            "id": "abc",
            "title": "t",
            "subreddit": "pics",
            "author": "a",
            "over_18": False,
            "score": 1,
            "created_utc": 0,
        }
        return SimpleNamespace(**(base | fields))

    async def test_gallery_skips_parsers(self):
        submission = self._submission(
            url="https://www.reddit.com/gallery/abc",
            is_gallery=True,
            gallery_data={"items": [{"media_id": "b"}, {"media_id": "a"}]},
            media_metadata={
                "a": {"status": "valid", "s": {"u": "https://preview.redd.it/a.jpg"}},
                "b": {"status": "valid", "s": {"u": "https://preview.redd.it/b.jpg"}},
            },
        )
        result, mock_find = await self._find(submission)
        self.assertEqual(
            result, ["https://preview.redd.it/b.jpg", "https://preview.redd.it/a.jpg"]
        )
        mock_find.assert_not_awaited()

    async def test_reddit_image_skips_parsers(self):
        submission = self._submission(url="https://i.redd.it/abc.jpg")
        result, mock_find = await self._find(submission)
        self.assertEqual(result, ["https://i.redd.it/abc.jpg"])
        mock_find.assert_not_awaited()

    async def test_gallery_without_listing_data_falls_back(self):
        # a listing object that lacks gallery_data must still be handled, by
        # the parsers fetching the post
        submission = self._submission(
            url="https://www.reddit.com/gallery/abc", is_gallery=True
        )
        result, mock_find = await self._find(submission)
        self.assertEqual(result, ["https://parsed/1"])
        mock_find.assert_awaited_once()

    async def test_link_post_uses_parsers(self):
        submission = self._submission(url="https://imgur.com/a/xyz")
        result, mock_find = await self._find(submission)
        self.assertEqual(result, ["https://parsed/1"])
        mock_find.assert_awaited_once()
