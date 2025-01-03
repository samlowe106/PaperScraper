import asyncio
import os
import unittest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, mock_open, patch

import pytest

import core
from core import SubmissionWrapper
from core.reddit.reddit import _from_source
from tests import SubmissionWrapperFactory


class TestSignIn(unittest.TestCase):
    @patch("praw.Reddit")
    def test_sign_in(self, mock_praw_reddit):
        # Assert correct call is made when no arguments passed
        core.reddit.sign_in()
        mock_praw_reddit.assert_called_with(
            client_id="mock reddit client id",
            client_secret="mock reddit client secret",
            user_agent="PaperScraper",
        )

        # Assert correct call is made with only username
        core.reddit.sign_in(username="username")
        mock_praw_reddit.assert_called_with(
            client_id="mock reddit client id",
            client_secret="mock reddit client secret",
            user_agent="PaperScraper",
        )

        # Assert correct call is made with only password
        core.reddit.sign_in(password="password")
        mock_praw_reddit.assert_called_with(
            client_id="mock reddit client id",
            client_secret="mock reddit client secret",
            user_agent="PaperScraper",
        )

        # Assert correct call is made with username and password
        core.reddit.sign_in(username="username", password="password")
        mock_praw_reddit.assert_called_with(
            client_id="mock reddit client id",
            client_secret="mock reddit client secret",
            user_agent="PaperScraper",
            username="username",
            password="password",
        )


class TestSubmissionWrapper(unittest.TestCase):
    def test_constructor(self):
        submission_mock = Mock()
        submission_mock.title = "mock ?? title: \\"
        submission_mock.subreddit = uuid.uuid4()
        submission_mock.url = str(uuid.uuid4())
        submission_mock.author = str(uuid.uuid4())
        submission_mock.over_18 = False
        submission_mock.score = 10
        submission_mock.created_utc = datetime.now()
        submission_mock.saved = Mock()

        client_mock = Mock()

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
    def test_download_all_organized(
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
        result = asyncio.run(
            wrapper.download_all(
                directory=directory, client=httpx_client_mock, organize=False
            )
        )

        os_listdir_mock.assert_called_with(directory)

        print(result)

        for key in expected.keys():
            httpx_client_mock.get.assert_called_with(key, timeout=10)
        os_makedirs_mock.assert_called_with(
            os.path.join(directory, wrapper.subreddit), exist_ok=True
        )
        for value in expected.values():
            open_mock.assert_called_with(value, "wb")
        self.assertDictEqual(result, expected)


class TestLog(unittest.TestCase):
    @patch("builtins.open", new_callable=mock_open, read_data="data")
    @patch("json.dump")
    def test_log(self, mock_json_dump, mock_file):
        wrapper = SubmissionWrapperFactory()
        wrapper.log("foo.file")
        mock_file.assert_called_with("foo.file", "a", encoding="utf-8")
        mock_json_dump.assert_called_with(
            {
                "title": wrapper._submission.title,
                "id": wrapper._submission.id,
                "url": wrapper._submission.url,
                "recognized_urls": wrapper.urls,
                "exception": "",
            },
            mock_file(),
        )

    @patch("builtins.open", new_callable=mock_open, read_data="data")
    @patch("json.dump")
    def test_log_with_exception(self, mock_json_dump, mock_file):
        wrapper = SubmissionWrapperFactory()
        wrapper.log("foo.file", exception="mock exception")
        mock_file.assert_called_once_with("foo.file", "a", encoding="utf-8")
        mock_json_dump.assert_called_with(
            {
                "title": wrapper._submission.title,
                "id": wrapper._submission.id,
                "url": wrapper._submission.url,
                "recognized_urls": wrapper.urls,
                "exception": "mock exception",
            },
            mock_file(),
        )

    def test_summary_string(self):
        # TODO
        pass


class TestFromSource(unittest.IsolatedAsyncioTestCase):

    async def test_requires_nonnegative_amount(self):
        with pytest.raises(ValueError):
            await _from_source(source="mock source", amount=-1, client="mock client")

    async def test_requires_nonzero_amount(self):
        with pytest.raises(ValueError):
            await _from_source(source="mock source", amount=0, client="mock client")

    @patch("core.SubmissionWrapper", wraps=lambda s, client, dry: (s))
    async def test_handles_exhaustion(self, mock_submission_wrapper):
        # amount is 10, generates only 4, two are valid, two are invalid
        mock_valid_1 = MagicMock()
        mock_valid_2 = MagicMock()
        mock_invalid_1 = MagicMock()
        mock_invalid_2 = MagicMock()
        mock_valid_1.urls = ["mock url"]
        mock_valid_2.urls = ["mock url"]
        mock_invalid_1.urls = []
        mock_invalid_2.urls = []
        mock_source = MagicMock()
        mock_source.return_value = iter(
            [mock_valid_1, mock_invalid_1, mock_valid_2, mock_invalid_2]
        )

        result = await _from_source(source=mock_source, amount=10, client="mock client")
        # Instead of wrapping submissions in a submission wrapper
        #  the mocked SubmissionWrapper just wraps the mocks in a tuple
        mock_submission_wrapper.assert_called_with(
            mock_valid_1, client="mock client", dry=True
        )
        mock_submission_wrapper.assert_called_with(
            mock_invalid_1, client="mock client", dry=True
        )
        mock_submission_wrapper.assert_called_with(
            mock_valid_2, client="mock client", dry=True
        )
        mock_submission_wrapper.assert_called_with(
            mock_invalid_2, client="mock client", dry=True
        )
        self.assertListEqual(result, [(mock_valid_1), (mock_valid_2)])

    @patch("core.SubmissionWrapper", wraps=lambda s, client, dry: (s))
    async def test_handles_not_enough_valid_submissions(self, mock_submission_wrapper):
        """The case where the amount contains more submissions than the amount required, but not enough are valid"""
        mock_valid_1 = MagicMock()
        mock_valid_2 = MagicMock()
        mock_invalid_1 = MagicMock()
        mock_invalid_2 = MagicMock()
        mock_invalid_3 = MagicMock()
        mock_valid_1.urls = ["mock url"]
        mock_valid_2.urls = ["mock url"]
        mock_invalid_1.urls = []
        mock_invalid_2.urls = []
        mock_invalid_3.urls = []
        mock_source = MagicMock()
        # amount is 3, list generates 5 but only 2 are valid. should have to request two batches
        mock_source.return_value = iter(
            [mock_valid_1, mock_invalid_1, mock_valid_2, mock_invalid_2, mock_invalid_3]
        )

        result = await _from_source(source=mock_source, amount=10, client="mock client")
        mock_submission_wrapper.assert_called_with(
            mock_valid_1, client="mock client", dry=True
        )
        mock_submission_wrapper.assert_called_with(
            mock_invalid_1, client="mock client", dry=True
        )
        mock_submission_wrapper.assert_called_with(
            mock_valid_2, client="mock client", dry=True
        )
        mock_submission_wrapper.assert_called_with(
            mock_invalid_2, client="mock client", dry=True
        )
        mock_submission_wrapper.assert_called_with(
            mock_invalid_3, client="mock client", dry=True
        )
        self.assertListEqual(result, [(mock_valid_1), (mock_valid_2)])


class TestFromSaved(unittest.IsolatedAsyncioTestCase):

    @patch("core.reddit.reddit._from_source")
    async def test_from_saved(self, mock_from_source):
        mock_redditor = MagicMock()
        mock_redditor.saved.return_value = object()
        expected_score = None
        expected_age = None
        expected_amount = 10
        mock_client = Mock()

        mock_from_source.return_value = object()
        result = await core.from_saved(mock_redditor, "mock client")

        mock_redditor.saved.assert_called_once_with(
            limit=None, score=expected_score, age=expected_age
        )

        mock_from_source.assert_called_once_with(
            mock_redditor.saved.return_value,
            mock_client,
            amount=expected_amount,
            dry=True,
        )

        self.assertEqual(result, mock_from_source.return_value)


class TestFromSubreddit(unittest.IsolatedAsyncioTestCase):
    @patch("core.reddit.reddit._from_source")
    async def test_from_subreddit(self, mock_from_source):
        expected_amount = 10
        expected_client = "mock client"
        expected_score = None
        expected_age = None

        mock_sort_by = Mock()
        mock_sort_by.return_value = object()
        mock_from_source.return_value = object()

        mock_reddit = MagicMock()
        mock_reddit.subreddit.return_value = object()

        result = await core.from_subreddit(
            mock_reddit, "r/mock_subreddit", mock_sort_by, expected_client
        )

        self.assertEqual(result, mock_from_source.return_value)

        mock_reddit.subreddit.assert_called_once_with("mock_subreddit")

        mock_sort_by.assert_called_once_with(
            mock_reddit.subreddit.return_value, score=expected_score, age=expected_age
        )

        mock_from_source.assert_called_once_with(
            mock_sort_by.return_value,
            expected_client,
            amount=expected_amount,
            dry=True,
        )

        self.assertEqual(result, mock_from_source.return_value)


if __name__ == "__main__":
    unittest.main()
