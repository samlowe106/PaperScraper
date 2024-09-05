import unittest
from unittest.mock import MagicMock

from core.parsers.imgur import _split_imgur_url, imgur_parser


class TestSplitImgurURL(unittest.TestCase):
    """Test the regex/function that splits imgur urls into their components"""

    # TODO: creating the urls and the expected results is a bit complicated for a test case
    #   maybe simplify it at the cost of a lot of repeated code

    expected_templates = [
        {
            "protocol": "https://",
            "direct_link": "",
            "base_url": "imgur.com/",
            "link_type": None,
            "link_id": "aB12c3",
        },
        {
            "protocol": "http://",
            "direct_link": "",
            "base_url": "imgur.com/",
            "link_type": None,
            "link_id": "XYz4zyX",
        },
    ]

    def test_regex_matches_album(self):
        # url1 = "{protocol}{direct_link}{base_url}{link_type}{link_id}"
        expected = self.expected_template.copy()
        expected[0]["link_type"] = "a/"  # "https://imgur.com/a/aB12c3"
        expected[1]["link_type"] = "a/"  # "https://imgur.com/a/XYz4zyX"

        url1 = "".join(expected[0].values())
        url2 = "".join(expected[1].values())

        match_dict = _split_imgur_url(url1)
        self.assertDictEqual(match_dict, expected[0])
        match_dict = _split_imgur_url(url2)
        self.assertDictEqual(match_dict, expected[1])

    def test_regex_matches_gallery(self):
        expected = self.expected_template.copy()
        expected[0]["link_type"] = "gallery/"
        expected[1]["link_type"] = "gallery/"

        url1 = "".join(expected[0].values())  # "https://imgur.com/gallery/aB12c3"
        url2 = "".join(expected[1].values())  # "https://imgur.com/gallery/XYz4zyX"

        match_dict = _split_imgur_url(url1)
        self.assertDictEqual(match_dict, expected[0])
        match_dict = _split_imgur_url(url2)
        self.assertDictEqual(match_dict, expected[1])

    def test_regex_matches_non_direct_single_image(self):
        expected = self.expected_template.copy()
        expected[0]["link_type"] = ""
        expected[1]["link_type"] = ""

        url1 = "".join(expected[0].values())  # "https://imgur.com/aB12c3"
        url2 = "".join(expected[1].values())  # "https://imgur.com/XYz4zyX"

        match_dict = _split_imgur_url(url1)
        self.assertDictEqual(match_dict, expected[0])
        match_dict = _split_imgur_url(url2)
        self.assertDictEqual(match_dict, expected[1])

    def test_regex_matches_direct_single_image(self):
        expected = self.expected_template.copy()
        expected[0]["direct_link"] = "i."
        expected[0]["link_type"] = ""
        expected[1]["direct_link"] = "i."
        expected[1]["link_type"] = ""

        url1 = "".join(expected[0].values())  # "https://i.imgur.com/aB12c3"
        url2 = "".join(expected[1].values())  # "https://i.imgur.com/XYz4zyX"

        match_dict = _split_imgur_url(url1)
        self.assertDictEqual(match_dict, expected[0])
        match_dict = _split_imgur_url(url2)
        self.assertDictEqual(match_dict, expected[1])

    def test_does_not_match_other(self):
        self.assertIsNone(_split_imgur_url("https://api.imgur.com/3/"))
        self.assertIsNone(_split_imgur_url("https://google.com"))
        self.assertIsNone(_split_imgur_url(""))


class TestImgurParser(unittest.TestCase):
    """
    Because this relies on the structure of imgur's website,
    we have to actually make http requests to imgur to test this.
    We also need to avoid spamming imgur with requests, so we'll
    take snapshots of the responses and use those to test
    """

    def test_handles_single_image(self):
        # TODO
        pass

    def test_handles_album(self):
        # TODO
        pass

    def test_handles_gallery(self):
        # TODO
        pass

    def test_ignores_non_imgur(self):
        result = imgur_parser("https://example.com", MagicMock())
        self.assertEqual(result, set())
        result = imgur_parser("http://google.com", MagicMock())
        self.assertEqual(result, set())
        result = imgur_parser("https://i.reddit.com", MagicMock())
        self.assertEqual(result, set())
        pass


if __name__ == "__main__":
    unittest.main()
