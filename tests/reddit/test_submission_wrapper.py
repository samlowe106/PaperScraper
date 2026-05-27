import unittest

# from datetime import datetime
from unittest.mock import AsyncMock, mock_open, patch

from tests import SubmissionWrapperFactory


class TestFindUrls(unittest.IsolatedAsyncioTestCase):

    async def test_find_urls(self):
        wrapped = SubmissionWrapperFactory()
        await wrapped.find_urls()


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


class TestLog(unittest.TestCase):

    @patch("json.dump")
    def test_log_no_exception(self, mock_json_dump):

        wrapped = SubmissionWrapperFactory()

        log_file_path = "log/path.txt"

        m = mock_open()
        file_handle = m.return_value.__enter__.return_value

        with patch("builtins.open", m):
            wrapped.log(log_file_path)

        m.assert_called_once_with(log_file_path, "a", encoding="utf-8")

        mock_json_dump.assert_called_once_with(
            {
                "title": wrapped._submission.title,
                "id": wrapped._submission.id,
                "url": wrapped._submission.url,
                "recognized_urls": wrapped.urls,
                "exception": "",
            },
            file_handle,
        )

    @patch("json.dump")
    def test_log_with_exception(self, mock_json_dump):

        wrapped = SubmissionWrapperFactory()

        log_file_path = "log/path.txt"

        m = mock_open()
        file_handle = m.return_value.__enter__.return_value

        mock_exception = Exception("Mock exception message")

        with patch("builtins.open", m):
            wrapped.log(log_file_path, mock_exception)

        m.assert_called_once_with(log_file_path, "a", encoding="utf-8")

        mock_json_dump.assert_called_once_with(
            {
                "title": wrapped._submission.title,
                "id": wrapped._submission.id,
                "url": wrapped._submission.url,
                "recognized_urls": wrapped.urls,
                "exception": mock_exception,
            },
            file_handle,
        )


class TestHasUrls(unittest.TestCase):

    def test_has_urls_empty(self):
        wrapped = SubmissionWrapperFactory()
        wrapped.urls = set()
        self.assertFalse(wrapped.has_urls())

    def test_has_urls_nonempty(self):
        wrapped = SubmissionWrapperFactory()
        wrapped.urls = set("example_url")
        self.assertTrue(wrapped.has_urls())
