import json
import unittest
from unittest.mock import patch

import httpx

from src.parsing.flickr import _decode_base58, _get_flickr_photo_id, flickr_parser
from tests import mock_http_bundle

# the shape flickr.photos.getSizes returns with nojsoncallback=1 (dimensions
# really do arrive as a mix of numbers and strings)
_SIZES_RESPONSE = {
    "sizes": {
        "canblog": 0,
        "canprint": 0,
        "candownload": 1,
        "size": [
            {
                "label": "Square",
                "width": 75,
                "height": 75,
                "source": "https://live.staticflickr.com/1/1_s.jpg",
            },
            {
                "label": "Original",
                "width": "4000",
                "height": "3000",
                "source": "https://live.staticflickr.com/1/1_o.jpg",
            },
            {
                "label": "Large",
                "width": "1024",
                "height": "768",
                "source": "https://live.staticflickr.com/1/1_b.jpg",
            },
        ],
    },
    "stat": "ok",
}


class TestGetFlickrPhotoID(unittest.TestCase):

    def test_direct_photo(self):
        for url in [
            "https://www.flickr.com/photos/mockuser/12345/",
            # no trailing slash used to go unrecognized
            "https://www.flickr.com/photos/mockuser/12345",
            "https://flickr.com/photos/mockuser/12345/in/album-72157/",
        ]:
            with self.subTest(url):
                self.assertEqual(_get_flickr_photo_id(url), "12345")

    def test_non_photo_pages(self):
        for url in [
            "https://example.com",
            # "albums" used to be taken as a photo id
            "https://www.flickr.com/photos/mockuser/albums/",
            "https://www.flickr.com/photos/mockuser/",
        ]:
            with self.subTest(url):
                self.assertIsNone(_get_flickr_photo_id(url))

    def test_short_url_is_decoded_without_a_request(self):
        self.assertEqual(
            _get_flickr_photo_id("https://flic.kr/p/21"), _decode_base58("21")
        )


class TestDecodeBase58(unittest.TestCase):

    def test_digits(self):
        # "1" is zero and "2" is one in flickr's alphabet
        self.assertEqual(_decode_base58("1"), "0")
        self.assertEqual(_decode_base58("2"), "1")
        self.assertEqual(_decode_base58("21"), "58")
        self.assertEqual(_decode_base58("Z"), "57")

    def test_rejects_characters_outside_alphabet(self):
        # 0, O, I and l are left out because they look alike
        for char in "0OIl":
            self.assertIsNone(_decode_base58(char))


@patch.dict("os.environ", {"FLICKR_CLIENT_ID": "mock_api_key"})
class TestFlickrParser(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.requests: list[httpx.Request] = []

    def _bundle(self, status=200, body=_SIZES_RESPONSE):
        def handler(request):
            self.requests.append(request)
            return httpx.Response(status, json=body)

        return mock_http_bundle(handler)

    async def test_returns_largest_size(self):
        result = await flickr_parser(
            "https://www.flickr.com/photos/u/12345/", self._bundle()
        )
        self.assertEqual(result, ["https://live.staticflickr.com/1/1_o.jpg"])

        (request,) = self.requests
        self.assertEqual(
            dict(request.url.params),
            {
                "api_key": "mock_api_key",
                "format": "json",
                "nojsoncallback": "1",
                # getInfo returns a different shape and used to raise KeyError
                "method": "flickr.photos.getSizes",
                "photo_id": "12345",
            },
        )

    async def test_no_request_for_non_flickr_url(self):
        self.assertEqual(await flickr_parser("https://example.com", self._bundle()), [])
        self.assertEqual(self.requests, [])

    @patch.dict("os.environ", {}, clear=True)
    async def test_returns_empty_without_api_key(self):
        result = await flickr_parser(
            "https://www.flickr.com/photos/u/12345/", self._bundle()
        )
        self.assertEqual(result, [])
        self.assertEqual(self.requests, [])

    async def test_returns_empty_on_non_200(self):
        result = await flickr_parser(
            "https://www.flickr.com/photos/u/12345/", self._bundle(status=500)
        )
        self.assertEqual(result, [])

    async def test_api_error_returned_as_200(self):
        # flickr reports errors with stat "fail" and a 200 status
        body = {"stat": "fail", "code": 1, "message": "Photo not found"}
        result = await flickr_parser(
            "https://www.flickr.com/photos/u/12345/", self._bundle(body=body)
        )
        self.assertEqual(result, [])

    async def test_download_not_allowed(self):
        body = json.loads(json.dumps(_SIZES_RESPONSE))
        body["sizes"]["candownload"] = 0
        result = await flickr_parser(
            "https://www.flickr.com/photos/u/12345/", self._bundle(body=body)
        )
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
