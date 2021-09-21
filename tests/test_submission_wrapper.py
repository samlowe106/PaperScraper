from src.model.submission_wrapper import SubmissionWrapper
import json
import unittest


class TestSubmissionWrapper(unittest.TestCase):

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
