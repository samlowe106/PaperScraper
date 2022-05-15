import json
import unittest
import os
from praw.models import Submission
from PaperScraper.core.models import SubmissionSource
from PaperScraper.core import sign_in
from PaperScraper.core.models.submission_wrapper import SubmissionWrapper


class TestSubmissionSource(unittest.TestCase):
    """Verifies that SubmissionWrapper works as expected"""

    def test_iter_subreddit(self):
        """Tests that __iter__ behaves as expected"""

        subreddit_posts = {SubmissionWrapper(Submission(url)) for url in []}

        reddit = sign_in()

        source = SubmissionSource.Builder().from_user_saved(reddit).build()


    def test_iter_saved(self):
        """Tests that __iter__ behaves as expected"""

        posts_direct = set()
        for url in []:
            submission = Submission(url)
            submission.save()
            posts_direct.add(SubmissionWrapper(submission))

        reddit = sign_in(os.environ["dummy_user"], os.environ["dummy_pass"])

        posts_source = SubmissionSource.Builder().from_user_saved(reddit).build()

        for direct, sourced in zip(posts_direct, posts_source):
            self.assertEqual(direct, sourced)