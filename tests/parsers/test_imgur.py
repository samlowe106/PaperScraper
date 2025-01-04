import unittest
from unittest.mock import AsyncMock

from core.parsers.imgur import _split_imgur_url, imgur_parser


class TestSplitImgurURL(unittest.TestCase):
    """Test the regex/function that splits imgur urls into their components"""

    def test_regex_matches_album(self):
        url1 = "www.imgur.com/a/XYz4zyX"
        url2 = "http://imgur.com/a/XYz4zyX"
        url3 = "https://imgur.com/a/aB12c3"
        url4 = "http://www.imgur.com/a/XYz4zyX"
        url5 = "https://www.imgur.com/a/aB12c3"

        expected1 = {
            "direct_link": None,
            "base_url": "imgur.com",
            "link_type": "/a/",
            "link_id": "XYz4zyX",
        }
        expected2 = {
            "direct_link": None,
            "base_url": "imgur.com",
            "link_type": "/a/",
            "link_id": "aB12c3",
        }

        self.assertDictEqual(_split_imgur_url(url1), expected1)
        self.assertDictEqual(_split_imgur_url(url2), expected1)
        self.assertDictEqual(_split_imgur_url(url3), expected2)
        self.assertDictEqual(_split_imgur_url(url4), expected1)
        self.assertDictEqual(_split_imgur_url(url5), expected2)

    def test_regex_matches_gallery(self):
        url1 = "www.imgur.com/gallery/XYz4zyX"
        url2 = "http://imgur.com/gallery/XYz4zyX"
        url3 = "https://imgur.com/gallery/aB12c3"
        url4 = "http://www.imgur.com/gallery/XYz4zyX"
        url5 = "https://www.imgur.com/gallery/aB12c3"

        expected1 = {
            "direct_link": None,
            "base_url": "imgur.com",
            "link_type": "/gallery/",
            "link_id": "XYz4zyX",
        }
        expected2 = {
            "direct_link": None,
            "base_url": "imgur.com",
            "link_type": "/gallery/",
            "link_id": "aB12c3",
        }

        self.assertDictEqual(_split_imgur_url(url1), expected1)
        self.assertDictEqual(_split_imgur_url(url2), expected1)
        self.assertDictEqual(_split_imgur_url(url3), expected2)
        self.assertDictEqual(_split_imgur_url(url4), expected1)
        self.assertDictEqual(_split_imgur_url(url5), expected2)

    def test_regex_matches_non_direct_single_image(self):
        url1 = "www.imgur.com/XYz4zyX"
        url2 = "http://imgur.com/XYz4zyX"
        url3 = "https://imgur.com/aB12c3"
        url4 = "http://www.imgur.com/XYz4zyX"
        url5 = "https://www.imgur.com/aB12c3"

        expected1 = {
            "direct_link": None,
            "base_url": "imgur.com",
            "link_type": "/",
            "link_id": "XYz4zyX",
        }
        expected2 = {
            "direct_link": None,
            "base_url": "imgur.com",
            "link_type": "/",
            "link_id": "aB12c3",
        }

        self.assertDictEqual(_split_imgur_url(url1), expected1)
        self.assertDictEqual(_split_imgur_url(url2), expected1)
        self.assertDictEqual(_split_imgur_url(url3), expected2)
        self.assertDictEqual(_split_imgur_url(url4), expected1)
        self.assertDictEqual(_split_imgur_url(url5), expected2)

    def test_regex_matches_direct_single_image(self):
        url1 = "www.i.imgur.com/XYz4zyX"
        url2 = "http://i.imgur.com/XYz4zyX"
        url3 = "https://i.imgur.com/aB12c3"
        url4 = "http://www.i.imgur.com/XYz4zyX"
        url5 = "https://www.i.imgur.com/aB12c3"

        expected1 = {
            "direct_link": "i.",
            "base_url": "imgur.com",
            "link_type": "/",
            "link_id": "XYz4zyX",
        }
        expected2 = {
            "direct_link": "i.",
            "base_url": "imgur.com",
            "link_type": "/",
            "link_id": "aB12c3",
        }

        self.assertDictEqual(_split_imgur_url(url1), expected1)
        self.assertDictEqual(_split_imgur_url(url2), expected1)
        self.assertDictEqual(_split_imgur_url(url3), expected2)
        self.assertDictEqual(_split_imgur_url(url4), expected1)
        self.assertDictEqual(_split_imgur_url(url5), expected2)

    def test_does_not_match_other(self):
        self.assertIsNone(_split_imgur_url("https://api.imgur.com/3/"))
        self.assertIsNone(_split_imgur_url("https://google.com"))
        self.assertIsNone(_split_imgur_url(""))


class TestImgurParser(unittest.IsolatedAsyncioTestCase):
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

    async def test_ignores_non_imgur(self):
        mock_client = AsyncMock()

        async def mock_get(url):
            mock_response = AsyncMock()
            mock_response.url = url
            return mock_response

        mock_client.get = mock_get
        result = await imgur_parser("https://example.com", mock_client)
        self.assertEqual(result, set())
        result = await imgur_parser("http://google.com", mock_client)
        self.assertEqual(result, set())
        result = await imgur_parser("https://i.reddit.com", mock_client)
        self.assertEqual(result, set())


if __name__ == "__main__":
    unittest.main()
