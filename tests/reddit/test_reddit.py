import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from tests import SubmissionWrapperFactory


class TestLogRecord(unittest.TestCase):

    def test_builds_record(self):
        wrapper = SubmissionWrapperFactory()
        wrapper._submission.id = "abc123"
        wrapper.urls = {"https://imgur.com/2", "https://imgur.com/1"}

        record = wrapper.log_record()

        self.assertEqual(record["id"], "abc123")
        self.assertEqual(record["url"], wrapper._submission.url)
        self.assertEqual(record["exception"], "")
        # set is serialized as a sorted list
        self.assertEqual(
            record["recognized_urls"],
            ["https://imgur.com/1", "https://imgur.com/2"],
        )

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
            mock_find.return_value = {"https://img/1", "https://img/2"}
            result = await wrapper.find_urls(mock_clients)

        mock_find.assert_awaited_once_with("https://example.com/post", mock_clients)
        self.assertEqual(wrapper.urls, {"https://img/1", "https://img/2"})
        self.assertEqual(result, {"https://img/1", "https://img/2"})
        self.assertTrue(wrapper.has_urls())

    async def test_find_urls_empty(self):
        wrapper = SubmissionWrapperFactory(url="https://example.com/post")
        mock_clients = MagicMock()

        with patch(
            "src.reddit.submission_wrapper.parse_find_urls",
            new_callable=AsyncMock,
        ) as mock_find:
            mock_find.return_value = set()
            await wrapper.find_urls(mock_clients)

        self.assertEqual(wrapper.urls, set())
        self.assertFalse(wrapper.has_urls())
