import unittest

import httpx

from src.core import get_response_file_extension


def _response(content_type: str | None, url: str = "https://example.com/x"):
    headers = {} if content_type is None else {"Content-Type": content_type}
    return httpx.Response(200, headers=headers, request=httpx.Request("GET", url))


class TestGetExtension(unittest.TestCase):

    def test_common_types(self):
        for content_type, extension in [
            ("image/gif", ".gif"),
            ("image/webp", ".webp"),
            ("video/mp4", ".mp4"),
            ("IMAGE/PNG", ".png"),
            # nonstandard, but servers send it
            ("image/jpg", ".jpg"),
        ]:
            with self.subTest(content_type):
                self.assertEqual(
                    get_response_file_extension(_response(content_type)), extension
                )

    def test_ignores_parameters(self):
        # used to come back as ".png; charset=binary"
        r = _response("image/png; charset=binary")
        self.assertEqual(get_response_file_extension(r), ".png")

    def test_missing_header_falls_back_to_url(self):
        # used to raise KeyError and fail the whole post
        r = _response(None, "https://example.com/a/b.JPG?x=1")
        self.assertEqual(get_response_file_extension(r), ".jpg")

    def test_unknown_type_and_no_url_extension(self):
        r = _response("application/x-nonsense", "https://example.com/a/b")
        self.assertEqual(get_response_file_extension(r), "")
