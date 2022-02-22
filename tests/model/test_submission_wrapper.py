from src.model.submission_wrapper import SubmissionWrapper
import json
import unittest
from praw.models import Submission
from typing import List, Tuple


class TestSubmissionWrapper(unittest.TestCase):
    """ """

    urls = ["https://www.reddit.com/r/ImaginaryFutureWar/comments/pvum2y/mech_sketch_by_daryl_mandryk/",
            "https://www.reddit.com/r/ImaginaryWorlds/comments/pv8b3p/fantasy_dreaming_by_michal_kv%C3%A1%C4%8D/",
            ]

    def initialize_posts_wrappers(self) -> List[Tuple(Submission, SubmissionWrapper)]:
        posts_wrappers = []
        for url in self.urls:
            post = Submission(url)
            wrapper = SubmissionWrapper(post)
            posts_wrappers.append((post, wrapper))
        return posts_wrappers
        

    def test_fields(self):
        for post, wrapper in self.initialize_posts_wrappers():
            self.assertEqual(post.title, wrapper.title)
            self.assertEqual(str(post.subreddit), wrapper.subreddit)
            self.assertEqual(post.url, wrapper.url)
            self.assertEqual(str(post.author), wrapper.author)


    def test_download_all(self):
        # TODO
        pass


    def test_download_image(self):
        # TODO
        pass


    def test_count_parsed(self):
        # TODO
        pass


    def test_fully_parsed(self):
        # TODO
        pass


    def test_log(self):
        # TODO
        with open("expected_log.json") as expected_log:
            json.dump({
                        "title"           : "",
                        "id"              : "",
                        "url"             : "",
                        "recognized_urls" : [()],
                    }, expected_log)

            with open("log.json") as actual_log:
                for expected, actual in zip(expected_log.read(), actual_log.read()):
                    self.assertEqual(expected, actual)


    def test_unsave(self):

        # log in

        for url in self.urls:
            # save the post 
            pass

        for post, wrapper in self.initialize_posts_wrappers():
            wrapper.unsave()
            self.assertFalse(post.saved()) # double check this method


    
    def test_format(self):
        wrapper = None # SubmissionWrapper
        self.assertEqual("", wrapper.format(""))
        self.assertEqual("%", wrapper.format("%%"))
        self.assertEqual("%%", wrapper.format("%%", token = "$"))
        

    def test_str(self):
        # TODO
        pass
