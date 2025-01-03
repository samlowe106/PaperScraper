import os
import unittest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

from core import SubmissionWrapper
from tests import SubmissionWrapperFactory


class TestConstructor(unittest.TestCase):
    def test_constructor(self):
        submission_mock = MagicMock()
        submission_mock.title = "mock ?? title: \\"
        submission_mock.subreddit = uuid.uuid4()
        submission_mock.url = str(uuid.uuid4())
        submission_mock.author = str(uuid.uuid4())
        submission_mock.over_18 = False
        submission_mock.score = 10
        submission_mock.created_utc = datetime.now()
        submission_mock.saved = MagicMock()

        client_mock = MagicMock()

        dry = True

        wrapper = SubmissionWrapper(submission_mock, client_mock, dry=dry)

        # Assert that the wrapper has the correct values
        self.assertEqual(wrapper.title, submission_mock.title)
        self.assertEqual(wrapper.subreddit, str(submission_mock.subreddit))
        self.assertEqual(wrapper.url, submission_mock.url)
        self.assertEqual(wrapper.author, submission_mock.author)
        self.assertEqual(wrapper.nsfw, submission_mock.over_18)
        self.assertEqual(wrapper.score, submission_mock.score)
        self.assertEqual(wrapper.created_utc, submission_mock.created_utc)
        self.assertEqual(wrapper.can_unsave, not dry)
        # Assert that the file title has the special characters removed
        self.assertEqual(wrapper.base_file_title, "mock title")
        # Assert values like responses and urls are not set
        self.assertIsNone(wrapper.response)
        self.assertEqual(wrapper.urls, set())
        # Assert that the submission is has not been unsaved
        submission_mock.unsave.assert_not_called()


class TestUnsave(unittest.TestCase):
    def test_unsave(self):
        # Assert SubmissionWrappers do not unsave posts when dry = True
        wrapper = SubmissionWrapperFactory()
        self.assertFalse(wrapper.unsave())
        wrapper._submission.unsave.assert_not_called()

        # Assert SubmissionWrappers do unsave posts when dry = False
        wrapper = SubmissionWrapperFactory(dry=False)
        self.assertTrue(wrapper.unsave())
        wrapper._submission.unsave.assert_called_once()

        # Assert SubmissionWrappers do unsave posts force = True
        wrapper = SubmissionWrapperFactory()
        self.assertTrue(wrapper.unsave(force=True))
        wrapper._submission.unsave.assert_called_once()

        # Assert SubmissionWrappers do unsave posts force = True
        wrapper = SubmissionWrapperFactory(dry=False)
        self.assertTrue(wrapper.unsave(force=True))
        wrapper._submission.unsave.assert_called_once()


class TestDownloadAll(unittest.IsolatedAsyncioTestCase):

    async def test_download_all_empty(self):
        # Assert that an empty list of urls returns an empty dictionary
        wrapper = SubmissionWrapperFactory()
        self.assertEqual(wrapper.urls, set())
        mock_client = MagicMock()
        mock_path = "mock path"
        self.assertEqual(await wrapper.download_all(mock_path, mock_client), dict())

    @patch("httpx.Response")
    @patch("os.makedirs")
    @patch("core.get_extension")
    @patch("builtins.open", new_callable=mock_open)
    async def test_download_all_unorganized(
        self,
        open_mock,
        get_extension_mock,
        os_makedirs_mock,
        httpx_response_mock,
    ):
        directory = "mock directory"
        httpx_client = AsyncMock()
        wrapper = SubmissionWrapperFactory()
        wrapper.urls = ["url1", "url2", "url3", "url4"]
        httpx_response_mock.content = "mock content"
        get_extension_mock.return_value = ".jpg"
        expected = {
            "url1": os.path.join(directory, "mock title.jpg"),
            "url2": os.path.join(directory, "mock title (1).jpg"),
            "url3": os.path.join(directory, "mock title (2).jpg"),
            "url4": os.path.join(directory, "mock title (3).jpg"),
        }
        result = await wrapper.download_all(
            title="mock title",
            directory=directory,
            client=httpx_client,
            organize=False,
        )
        mock_open.write.assert_called_with(httpx_response_mock.content)
        httpx_response_mock.assert_called_with("url1", timeout=10)
        httpx_response_mock.assert_called_with("url2", timeout=10)
        httpx_response_mock.assert_called_with("url3", timeout=10)
        httpx_response_mock.assert_called_with("url4", timeout=10)
        os_makedirs_mock.assert_called_with(directory, exist_ok=True)
        for value in expected.values():
            open_mock.assert_called_with(value, "wb")
        self.assertDictEqual(result, expected)

    @patch("os.makedirs")
    @patch("os.listdir")
    @patch("core.get_extension")
    @patch("builtins.open", new_callable=mock_open)
    async def test_download_all_organized(
        self,
        open_mock,
        get_extension_mock,
        os_listdir_mock,
        os_makedirs_mock,
    ):
        directory = "mock directory"
        httpx_client_mock = AsyncMock()

        class MockResponse:
            status_code = 200
            content = "mock content"

        os_listdir_mock.return_value = []

        httpx_client_mock.get.return_value = MockResponse()

        wrapper = SubmissionWrapperFactory()
        wrapper.subreddit = "mock subreddit"
        wrapper.title = "mock title"
        wrapper.urls = ["url1", "url2", "url3", "url4"]
        get_extension_mock.return_value = ".jpg"

        expected = {
            "url1": os.path.join(directory, wrapper.subreddit, "mock title.jpg"),
            "url2": os.path.join(directory, wrapper.subreddit, "mock title (1).jpg"),
            "url3": os.path.join(directory, wrapper.subreddit, "mock title (2).jpg"),
            "url4": os.path.join(directory, wrapper.subreddit, "mock title (3).jpg"),
        }
        result = await wrapper.download_all(
            directory=directory, client=httpx_client_mock, organize=False
        )

        os_listdir_mock.assert_called_with(directory)

        for key in expected.keys():
            httpx_client_mock.get.assert_called_with(key, timeout=10)
        os_makedirs_mock.assert_called_with(
            os.path.join(directory, wrapper.subreddit), exist_ok=True
        )
        for value in expected.values():
            open_mock.assert_called_with(value, "wb")
        self.assertDictEqual(result, expected)
