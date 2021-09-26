from src.model.submission_wrapper import SubmissionWrapper
import json
import unittest
from praw.models import Submission
from typing import List, Tuple


class TestSubmissionWrapper(unittest.TestCase):

    posts_wrappers: List[Tuple(Submission, SubmissionWrapper)] = []

    def __init__(self):
        # urls of reddit posts
        urls: List[str] = []
        for url in urls:
            post = Submission(url)
            wrapper = SubmissionWrapper(post)
            self.posts_wrappers.append((post, wrapper))
    

    def test_fields(self):
        for post, wrapper in self.posts_wrappers:
            self.assertEqual(post.title, wrapper.title)
            self.assertEqual(str(post.subreddit), wrapper.subreddit)
            self.assertEqual(post.url, wrapper.url)
            self.assertEqual(str(post.author), wrapper.author)


    def test_download_all(self):
        pass


    def test_download_image(self):
        pass


    def test_count_parsed(self):
        pass


    def test_fully_parsed(self):
        pass


    def test_log(self):
        
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


    def test_print_self(self):
        pass


    def test_unsave(self):
        pass

    
    def test_format(self):
        wrapper = None # SubmissionWrapper
        self.assertEqual("", wrapper.format(""))
        self.assertEqual("%", wrapper.format("%%"))
        self.assertEqual("%%", wrapper.format("%%", token = "$"))
        

    def test_str(self):
        pass
