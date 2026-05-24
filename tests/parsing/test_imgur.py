import json
import unittest
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from src.parsing.imgur import _split_imgur_url, imgur_parser


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
    Because this relies on the structure of imgur's website,
    we make real requests to imgur and rely on VCR to replay them
    when a cassette is available
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        with open("tests/parsing/imgur_test_data.json") as f:
            json_data = json.load(f)

        self.single_image_url = json_data["single_image"][0]["url"]
        self.album_url = json_data["album"][0]["url"]
        self.album_expected = set(json_data["album"][0]["expected"])
        self.gallery_url = json_data["gallery"][0]["url"]
        self.gallery_expected = set(json_data["gallery"][0]["expected"])

    @pytest.mark.vcr()
    async def test_handles_single_image(self):
        async with httpx.AsyncClient(headers={"User-Agent": "Mozilla/5.0"}) as client:
            mock_client_bundle = MagicMock()
            mock_client_bundle.http = client
            result = await imgur_parser(self.single_image_url, mock_client_bundle)

        self.assertEqual(result, {self.single_image_url})

    @pytest.mark.vcr()
    async def test_handles_album(self):
        async with httpx.AsyncClient(headers={"User-Agent": "Mozilla/5.0"}) as client:
            mock_client_bundle = MagicMock()
            mock_client_bundle.http = client

            result = await imgur_parser(self.album_url, mock_client_bundle)

        self.assertEqual(result, self.album_expected)

    @pytest.mark.vcr()
    async def test_handles_gallery(self):
        async with httpx.AsyncClient(headers={"User-Agent": "Mozilla/5.0"}) as client:
            mock_client_bundle = MagicMock()
            mock_client_bundle.http = client
            result = await imgur_parser(self.gallery_url, mock_client_bundle)

        self.assertEqual(result, self.gallery_expected)

    async def test_ignores_non_imgur(self):
        mock_client = AsyncMock()

        async def mock_get(url, headers=None):
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
