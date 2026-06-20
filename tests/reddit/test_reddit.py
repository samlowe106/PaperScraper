import json
import os
import tempfile
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from tests import SubmissionWrapperFactory


class TestLog(unittest.IsolatedAsyncioTestCase):

    async def test_log_writes_json(self):
        wrapper = SubmissionWrapperFactory()
        wrapper._submission.id = "abc123"
        wrapper.urls = {"https://imgur.com/1", "https://imgur.com/2"}

        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "log.txt")
            await wrapper.log(path)
            with open(path, encoding="utf-8") as f:
                data = json.loads(f.read())

        self.assertEqual(data["id"], "abc123")
        self.assertEqual(data["url"], wrapper._submission.url)
        self.assertEqual(data["exception"], "")
        # set is serialized as a sorted list
        self.assertEqual(
            data["recognized_urls"],
            ["https://imgur.com/1", "https://imgur.com/2"],
        )

    async def test_log_with_exception(self):
        wrapper = SubmissionWrapperFactory()
        wrapper._submission.id = "xyz"

        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "log.txt")
            await wrapper.log(path, exception="boom")
            with open(path, encoding="utf-8") as f:
                data = json.loads(f.read())

        self.assertEqual(data["exception"], "boom")
        self.assertEqual(data["recognized_urls"], [])


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
