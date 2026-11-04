import json
import unittest
from unittest.mock import MagicMock

import httpx
import pytest

from src.core import make_http_client
from src.parsing.imgur import _split_imgur_url, imgur_parser
from tests import mock_http_bundle


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
            "trailing_slash": None,
            "query_string": None,
        }
        expected2 = {
            "direct_link": None,
            "base_url": "imgur.com",
            "link_type": "/a/",
            "link_id": "aB12c3",
            "trailing_slash": None,
            "query_string": None,
        }

        self.assertDictEqual(_split_imgur_url(url1), expected1)
        self.assertDictEqual(_split_imgur_url(url2), expected1)
        self.assertDictEqual(_split_imgur_url(url3), expected2)
        self.assertDictEqual(_split_imgur_url(url4), expected1)
        self.assertDictEqual(_split_imgur_url(url5), expected2)

    def test_regex_matches_hyphenated_album(self):
        url1 = "https://www.imgur.com/a/minimal-star-wars-wallpapers-jlNpx"
        url2 = "https://imgur.com/a/minimal-star-wars-wallpapers-jlNpx"
        url3 = "http://www.imgur.com/a/minimal-star-wars-wallpapers-jlNpx"
        url4 = "http://imgur.com/a/minimal-star-wars-wallpapers-jlNpx"
        url5 = "imgur.com/a/minimal-star-wars-wallpapers-jlNpx"
        url6 = "www.imgur.com/a/minimal-star-wars-wallpapers-jlNpx"

        expected = {
            "direct_link": None,
            "base_url": "imgur.com",
            "link_type": "/a/",
            "link_id": "minimal-star-wars-wallpapers-jlNpx",
            "trailing_slash": None,
            "query_string": None,
        }

        self.assertDictEqual(_split_imgur_url(url1), expected)
        self.assertDictEqual(_split_imgur_url(url2), expected)
        self.assertDictEqual(_split_imgur_url(url3), expected)
        self.assertDictEqual(_split_imgur_url(url4), expected)
        self.assertDictEqual(_split_imgur_url(url5), expected)
        self.assertDictEqual(_split_imgur_url(url6), expected)

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
            "trailing_slash": None,
            "query_string": None,
        }
        expected2 = {
            "direct_link": None,
            "base_url": "imgur.com",
            "link_type": "/gallery/",
            "link_id": "aB12c3",
            "trailing_slash": None,
            "query_string": None,
        }

        self.assertDictEqual(_split_imgur_url(url1), expected1)
        self.assertDictEqual(_split_imgur_url(url2), expected1)
        self.assertDictEqual(_split_imgur_url(url3), expected2)
        self.assertDictEqual(_split_imgur_url(url4), expected1)
        self.assertDictEqual(_split_imgur_url(url5), expected2)

    def test_regex_matches_hyphenated_gallery(self):
        url1 = "https://www.imgur.com/gallery/feels-good-to-be-gangster-rSZlZ"
        url2 = "https://imgur.com/gallery/feels-good-to-be-gangster-rSZlZ"
        url3 = "http://www.imgur.com/gallery/feels-good-to-be-gangster-rSZlZ"
        url4 = "http://imgur.com/gallery/feels-good-to-be-gangster-rSZlZ"
        url5 = "imgur.com/gallery/feels-good-to-be-gangster-rSZlZ"
        url6 = "www.imgur.com/gallery/feels-good-to-be-gangster-rSZlZ"
        url6 = "https://imgur.com/gallery/feels-good-to-be-gangster-rSZlZ"

        expected = {
            "direct_link": None,
            "base_url": "imgur.com",
            "link_type": "/gallery/",
            "link_id": "feels-good-to-be-gangster-rSZlZ",
            "trailing_slash": None,
            "query_string": None,
        }

        self.assertDictEqual(_split_imgur_url(url1), expected)
        self.assertDictEqual(_split_imgur_url(url2), expected)
        self.assertDictEqual(_split_imgur_url(url3), expected)
        self.assertDictEqual(_split_imgur_url(url4), expected)
        self.assertDictEqual(_split_imgur_url(url5), expected)
        self.assertDictEqual(_split_imgur_url(url6), expected)

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
            "trailing_slash": None,
            "query_string": None,
        }
        expected2 = {
            "direct_link": None,
            "base_url": "imgur.com",
            "link_type": "/",
            "link_id": "aB12c3",
            "trailing_slash": None,
            "query_string": None,
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
            "trailing_slash": None,
            "query_string": None,
        }
        expected2 = {
            "direct_link": "i.",
            "base_url": "imgur.com",
            "link_type": "/",
            "link_id": "aB12c3",
            "trailing_slash": None,
            "query_string": None,
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
    Because this relies on the structure of imgur's API responses, these replay
    real recorded responses (VCR cassettes) through the production http client
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        with open("tests/parsing/imgur_test_data.json") as f:
            json_data = json.load(f)

        self.album_url = json_data["album"][0]["url"]
        self.album_expected = json_data["album"][0]["expected"]
        self.gallery_url = json_data["gallery"][0]["url"]
        self.gallery_expected = json_data["gallery"][0]["expected"]

    @staticmethod
    def _bundle(client):
        bundle = MagicMock()
        bundle.http = client
        return bundle

    @pytest.mark.vcr()
    async def test_handles_album(self):
        async with make_http_client() as client:
            result = await imgur_parser(self.album_url, self._bundle(client))

        # in album order
        self.assertEqual(result, self.album_expected)

    @pytest.mark.vcr()
    async def test_handles_gallery(self):
        async with make_http_client() as client:
            result = await imgur_parser(self.gallery_url, self._bundle(client))

        self.assertEqual(result, self.gallery_expected)


class TestImgurParserOffline(unittest.IsolatedAsyncioTestCase):
    """Edge cases, answered by a mock transport so no cassette or network is needed"""

    def setUp(self):
        self.requests: list[httpx.Request] = []

    def _bundle(self, status=200, body=None):
        def handler(request):
            self.requests.append(request)
            return httpx.Response(status, json=body or {})

        return mock_http_bundle(handler)

    async def test_ignores_non_imgur(self):
        bundle = self._bundle()
        for url in ["https://example.com", "http://google.com", "https://i.reddit.com"]:
            with self.subTest(url):
                self.assertEqual(await imgur_parser(url, bundle), [])
        self.assertEqual(self.requests, [])

    async def test_direct_link_returns_url_without_request(self):
        url = "https://i.imgur.com/abc123.jpg"
        self.assertEqual(await imgur_parser(url, self._bundle()), [url])
        self.assertEqual(self.requests, [])

    async def test_direct_gifv_link_becomes_mp4(self):
        # .gifv is an html page; the video is the .mp4 of the same name
        result = await imgur_parser("https://i.imgur.com/abc123.gifv", self._bundle())
        self.assertEqual(result, ["https://i.imgur.com/abc123.mp4"])

    async def test_single_image_uses_api(self):
        body = {"data": {"link": "https://i.imgur.com/abc123.png"}}
        for url in [
            "https://imgur.com/abc123",
            # a trailing slash used to raise IndexError
            "https://imgur.com/abc123/",
            # the extension used to be sent to the API as part of the id
            "https://imgur.com/abc123.png",
        ]:
            with self.subTest(url):
                self.requests.clear()
                result = await imgur_parser(url, self._bundle(body=body))
                self.assertEqual(result, ["https://i.imgur.com/abc123.png"])
                (request,) = self.requests
                self.assertEqual(
                    str(request.url), "https://api.imgur.com/3/image/abc123"
                )

    async def test_single_image_non_200(self):
        result = await imgur_parser("https://imgur.com/abc123", self._bundle(404))
        self.assertEqual(result, [])

    async def test_single_image_data_not_dict(self):
        bundle = self._bundle(body={"data": "not-a-dict"})
        self.assertEqual(await imgur_parser("https://imgur.com/abc123", bundle), [])

    async def test_album_non_200(self):
        result = await imgur_parser("https://imgur.com/a/abc123", self._bundle(500))
        self.assertEqual(result, [])

    async def test_gallery_non_200(self):
        result = await imgur_parser(
            "https://imgur.com/gallery/abc123", self._bundle(503)
        )
        self.assertEqual(result, [])

    async def test_album_skips_malformed_items(self):
        body = {"data": [{"link": "https://i.imgur.com/1.png"}, {"no": "link"}, 7]}
        result = await imgur_parser(
            "https://imgur.com/a/abc123", self._bundle(body=body)
        )
        self.assertEqual(result, ["https://i.imgur.com/1.png"])


if __name__ == "__main__":
    unittest.main()
