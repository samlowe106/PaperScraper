import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from core.parsers.flickr import _get_flickr_photo_id, flickr_parser


class TestFlickrRegex(unittest.TestCase):
    def test_regex_matches_direct_photo(self):
        result = asyncio.run(
            _get_flickr_photo_id(
                "https://www.flickr.com/photos/mockuser/12345/",
                AsyncMock(),
            )
        )
        self.assertEqual(result, "12345")

    def test_regex_matches_short_photo(self):
        mock_client = AsyncMock()
        response = AsyncMock()
        response.status_code = 200
        response.url = "https://www.flickr.com/photos/mockuser/12345/"
        mock_client.get.return_value = response

        result = asyncio.run(
            _get_flickr_photo_id("https://flic.kr/p/abcde", mock_client)
        )
        self.assertEqual(result, "12345")


class TestGetFlickrPhotoID(unittest.TestCase):
    def test_returns_none_for_invalid_url(self):
        result = asyncio.run(_get_flickr_photo_id("https://example.com", AsyncMock()))
        self.assertIsNone(result)


class TestFlickrParser(unittest.IsolatedAsyncioTestCase):
    @patch("core.parsers.flickr._get_flickr_photo_id")
    async def test_returns_empty_set_if_no_id(self, mock_get_flickr_photo_id):
        mock_get_flickr_photo_id.return_value = None
        result = flickr_parser("mock url", "mock client")
        self.assertEqual(await result, set())
        mock_get_flickr_photo_id.assert_called_once_with("mock url", "mock client")

    @patch.dict("os.environ", {"flickr_client_id": "mock_api_key"})
    @patch("core.parsers.flickr._get_flickr_photo_id", new_callable=AsyncMock)
    async def test_makes_api_call(self, mock_get_flickr_photo_id):
        mock_get_flickr_photo_id.return_value = "12345"

        response = AsyncMock()
        response.status_code = 200
        response.text = (
            'jsonFlickrApi({"sizes":{"candownload":1,"size":['
            '{"width":100,"height":100,"source":"https://i.flickr.com/1.jpg"},'
            '{"width":200,"height":200,"source":"https://i.flickr.com/2.jpg"}'
            "]}})"
        )

        mock_client = AsyncMock()
        mock_client.get.return_value = response

        result = await flickr_parser("mock url", mock_client)

        self.assertEqual(result, {"https://i.flickr.com/2.jpg"})
        expected_url = (
            "https://www.flickr.com/services/rest/?"
            "api_key=mock_api_key&format=json&method=flickr.photos.getInfo&photo_id=12345"
        )
        mock_client.get.assert_awaited_once_with(expected_url)


if __name__ == "__main__":
    unittest.main()
