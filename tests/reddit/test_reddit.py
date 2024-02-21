import os
import unittest
from unittest.mock import patch

import core
from tests import SubmissionWrapperFactory


class TestSignIn(unittest.TestCase):
    @patch("praw.Reddit")
    @patch.dict(
        os.environ,
        {
            "CLIENT_ID": "mock client id",
            "CLIENT_SECRET": "mock client secret",
        },
    )
    def test_sign_in(self, mock_praw_reddit):
        # Assert correct call is made when no arguments passed
        core.reddit.sign_in()
        mock_praw_reddit.assert_called_with(
            client_id="mock client id",
            client_secret="mock client secret",
            user_agent="PaperScraper",
        )

        # Assert correct call is made with only username
        core.reddit.sign_in(username="username")
        mock_praw_reddit.assert_called_with(
            client_id="mock client id",
            client_secret="mock client secret",
            user_agent="PaperScraper",
        )

        # Assert correct call is made with only password
        core.reddit.sign_in(password="password")
        mock_praw_reddit.assert_called_with(
            client_id="mock client id",
            client_secret="mock client secret",
            user_agent="PaperScraper",
        )

        # Assert correct call is made with username and password
        core.reddit.sign_in(username="username", password="password")
        mock_praw_reddit.assert_called_with(
            client_id="mock client id",
            client_secret="mock client secret",
            user_agent="PaperScraper",
            username="username",
            password="password",
        )


class TestSubmissionWrapper(unittest.TestCase):
    def test_constructor(self):
        # TODO
        # wrapper = SubmissionWrapperFactory()
        pass

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

    def test_download_all(self):
        # TODO
        pass

    @patch("open")
    @patch("json.dump")
    def test_log(self, mock_open, mock_json_dump):
        # TODO
        pass

    def test_summary_string(self):
        # TODO
        pass


class TestFromSaved(unittest.TestCase):
    # TODO

    def __init__(self):
        pass


class TestFromSubreddit(unittest.TestCase):
    # TODO

    def __init__(self):
        pass
