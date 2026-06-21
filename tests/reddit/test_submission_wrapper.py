import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from src.reddit.submission_wrapper import _get_with_retry
from tests import SubmissionWrapperFactory

# Note: log() and find_urls() are covered in tests/reddit/test_reddit.py


class TestGetWithRetry(unittest.IsolatedAsyncioTestCase):

    async def test_returns_response_on_success(self):
        resp = MagicMock(status_code=200)
        client = AsyncMock()
        client.get = AsyncMock(return_value=resp)
        result = await _get_with_retry(client, "u", backoff=0)
        self.assertIs(result, resp)
        self.assertEqual(client.get.await_count, 1)

    async def test_does_not_retry_hard_error(self):
        resp = MagicMock(status_code=404)  # 404 is a hard error, not retryable
        client = AsyncMock()
        client.get = AsyncMock(return_value=resp)
        result = await _get_with_retry(client, "u", attempts=3, backoff=0)
        self.assertIs(result, resp)
        self.assertEqual(client.get.await_count, 1)

    async def test_retries_transport_error_then_succeeds(self):
        ok = MagicMock(status_code=200)
        client = AsyncMock()
        client.get = AsyncMock(side_effect=[httpx.ConnectError("x"), ok])
        result = await _get_with_retry(client, "u", attempts=3, backoff=0)
        self.assertIs(result, ok)
        self.assertEqual(client.get.await_count, 2)

    async def test_retries_retryable_status_then_succeeds(self):
        ok = MagicMock(status_code=200)
        client = AsyncMock()
        client.get = AsyncMock(side_effect=[MagicMock(status_code=503), ok])
        result = await _get_with_retry(client, "u", attempts=3, backoff=0)
        self.assertIs(result, ok)

    async def test_returns_none_when_transport_errors_exhaust_attempts(self):
        client = AsyncMock()
        client.get = AsyncMock(side_effect=httpx.ConnectError("x"))
        result = await _get_with_retry(client, "u", attempts=2, backoff=0)
        self.assertIsNone(result)
        self.assertEqual(client.get.await_count, 2)


class TestUnsave(unittest.IsolatedAsyncioTestCase):

    async def test_calls_unsave(self):
        wrapper = SubmissionWrapperFactory()
        with patch.object(
            wrapper._submission,
            "unsave",
            new_callable=AsyncMock,
        ) as mock_unsave:

            await wrapper.unsave()
            mock_unsave.assert_awaited_once()


class TestDownload(unittest.IsolatedAsyncioTestCase):

    async def test_download_empty(self):
        # Assert that an empty list of urls returns an empty dictionary
        wrapper = SubmissionWrapperFactory()
        self.assertEqual(wrapper.urls, set())
        mock_client = AsyncMock()
        self.assertEqual(await wrapper.download(mock_client), list())

    async def test_download_skips_failed_urls(self):
        # a url that exhausts retries (None) is dropped; others still download
        good = MagicMock(status_code=200, content=b"data")
        good.headers = {"Content-type": "image/jpg"}

        def fake(client, url, **kwargs):
            return good if url == "good" else None

        wrapper = SubmissionWrapperFactory()
        wrapper.urls = ["good", "bad"]
        with patch(
            "src.reddit.submission_wrapper._get_with_retry",
            new_callable=AsyncMock,
            side_effect=fake,
        ):
            result = await wrapper.download(AsyncMock())

        self.assertEqual(result, [(b"data", ".jpg")])

    async def test_download_nonempty(self):
        mock_client = AsyncMock()

        urls_extensions = {
            "url1": "jpg",
            "url2": "png",
            "url3": "gif",
            "url4": "webm",
        }

        class MockResponse:
            def __init__(self, content_mock, file_ext="jpg"):
                self.status_code = 200
                self.content = content_mock
                self.headers = {"Content-type": f"image/{file_ext}"}

        async def mock_response_contents(mock_url, **kwargs):
            return MockResponse(
                mock_url + " mock content", file_ext=urls_extensions[mock_url]
            )

        mock_client.get.side_effect = mock_response_contents

        wrapper = SubmissionWrapperFactory()
        wrapper.subreddit = "mock subreddit"
        wrapper.title = "mock title"
        wrapper.urls = list(urls_extensions.keys())
        print(f"{wrapper.urls=}")

        contents_extensions = await wrapper.download(mock_client)

        expected = [
            ("url1 mock content", ".jpg"),
            ("url2 mock content", ".png"),
            ("url3 mock content", ".gif"),
            ("url4 mock content", ".webm"),
        ]

        print(mock_client.get.call_args_list)

        for url in urls_extensions.keys():
            mock_client.get.assert_any_call(url, timeout=10)

        self.assertListEqual(contents_extensions, expected)


class TestStr(unittest.TestCase):

    def test_str_contains_info(self):

        wrapper = SubmissionWrapperFactory()

        self.assertIn(wrapper.title, str(wrapper))
        self.assertIn(wrapper.subreddit, str(wrapper))
        self.assertIn(wrapper.author, str(wrapper))
        self.assertIn(wrapper.url, str(wrapper))


class TestHasUrls(unittest.TestCase):

    def test_has_urls_empty(self):
        wrapped = SubmissionWrapperFactory()
        wrapped.urls = set()
        self.assertFalse(wrapped.has_urls())

    def test_has_urls_nonempty(self):
        wrapped = SubmissionWrapperFactory()
        wrapped.urls = set("example_url")
        self.assertTrue(wrapped.has_urls())
