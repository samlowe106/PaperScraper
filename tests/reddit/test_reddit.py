import unittest
from unittest.mock import MagicMock, mock_open, patch

import pytest

import core
from core import SubmissionWrapper
from core.reddit.reddit import _from_source
from tests import SubmissionMockFactory, SubmissionWrapperFactory


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

    async def test_handles_exhaustion(self):
        # amount is 10, generates only 4, two are valid, two are invalid
        mock_valid_1 = SubmissionMockFactory()
        mock_valid_2 = SubmissionMockFactory()
        mock_invalid_1 = SubmissionMockFactory()
        mock_invalid_2 = SubmissionMockFactory()
        mock_source = iter([mock_valid_1, mock_invalid_1, mock_valid_2, mock_invalid_2])
        mock_client = "mock client"

        async def mock_find_urls(wrapper, client):
            if wrapper._submission == mock_valid_1:
                wrapper.urls = {"mock url 1"}
            if wrapper._submission == mock_valid_2:
                wrapper.urls = {"mock url 2"}

        with patch("core.SubmissionWrapper.find_urls", mock_find_urls):
            result = await _from_source(
                source=mock_source, amount=10, client=mock_client
            )

        for submission in [mock_valid_1, mock_valid_2, mock_invalid_1, mock_invalid_2]:
            submission.unsave.assert_not_called()

        for wrapper in result:
            print(wrapper)
            print(wrapper.urls)
            print(3 * "\n")

        expected1 = SubmissionWrapper(mock_valid_1, mock_client, dry=True)
        expected1.urls = {"mock url 1"}
        expected2 = SubmissionWrapper(mock_valid_2, mock_client, dry=True)
        expected2.urls = {"mock url 2"}

        self.assertListEqual(
            result,
            [expected1, expected2],
        )

    async def test_handles_not_enough_valid_submissions(self):
        """The case where the amount contains more submissions than the amount required, but not enough are valid"""
        mock_valid_1 = SubmissionMockFactory()
        mock_valid_2 = SubmissionMockFactory()
        mock_invalid_1 = SubmissionMockFactory()
        mock_invalid_2 = SubmissionMockFactory()
        mock_invalid_3 = SubmissionMockFactory()
        mock_invalid_4 = SubmissionMockFactory()
        mock_invalid_5 = SubmissionMockFactory()
        mock_client = "mock client"

        async def mock_find_urls(wrapper, client):
            if wrapper._submission == mock_valid_1:
                wrapper.urls = {"mock url 1"}
            if wrapper._submission == mock_valid_2:
                wrapper.urls = {"mock url 2"}

        # amount is 3, list generates 7 before exhaustion but only 2 are valid
        mock_source = iter(
            [
                mock_valid_1,
                mock_invalid_1,
                mock_invalid_2,
                mock_invalid_3,
                mock_invalid_4,
                mock_invalid_5,
                mock_valid_2,
            ]
        )

        with patch("core.SubmissionWrapper.find_urls", mock_find_urls):
            result = await _from_source(
                source=mock_source, amount=10, client=mock_client
            )

        for submission in [mock_valid_1, mock_valid_2, mock_invalid_1, mock_invalid_2]:
            submission.unsave.assert_not_called()

        expected1 = SubmissionWrapper(mock_valid_1, mock_client, dry=True)
        expected1.urls = {"mock url 1"}
        expected2 = SubmissionWrapper(mock_valid_2, mock_client, dry=True)
        expected2.urls = {"mock url 2"}

        self.assertListEqual(
            result,
            [expected1, expected2],
        )


class TestFromSaved(unittest.IsolatedAsyncioTestCase):

    @patch("core.reddit.reddit._from_source")
    async def test_from_saved(self, mock_from_source):
        mock_redditor = MagicMock()
        mock_redditor.saved.return_value = object()
        expected_score = None
        expected_age = None
        expected_amount = 10
        mock_client = MagicMock()

        mock_from_source.return_value = object()
        result = await core.from_saved(mock_redditor, mock_client)

        mock_redditor.saved.assert_called_once_with(
            limit=None,
            score=expected_score,
            age=expected_age,
        )

        mock_from_source.assert_called_once_with(
            mock_redditor.saved.return_value,
            mock_client,
            amount=expected_amount,
            dry=True,
            criteria=core.reddit.has_urls,
        )

        self.assertEqual(result, mock_from_source.return_value)


class TestFromSubreddit(unittest.IsolatedAsyncioTestCase):
    @patch("core.reddit.reddit._from_source")
    async def test_from_subreddit(self, mock_from_source):
        expected_amount = 10
        expected_client = "mock client"
        expected_score = None
        expected_age = None

        mock_sort_by = MagicMock()
        mock_sort_by.return_value = object()
        mock_from_source.return_value = object()

        mock_reddit = MagicMock()
        mock_reddit.subreddit.return_value = object()

        result = await core.from_subreddit(
            mock_reddit,
            "r/mock_subreddit",
            mock_sort_by,
            expected_client,
            criteria=core.reddit.has_urls,
        )

        self.assertEqual(result, mock_from_source.return_value)

        mock_reddit.subreddit.assert_called_once_with("mock_subreddit")

        mock_sort_by.assert_called_once_with(
            mock_reddit.subreddit.return_value,
            score=expected_score,
            age=expected_age,
        )

        mock_from_source.assert_called_once_with(
            mock_sort_by.return_value,
            expected_client,
            amount=expected_amount,
            dry=True,
            criteria=core.reddit.has_urls,
        )

        self.assertEqual(result, mock_from_source.return_value)


if __name__ == "__main__":
    unittest.main()
