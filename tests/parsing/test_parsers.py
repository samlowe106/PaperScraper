import unittest

import httpx

from src.parsing import find_urls, single_image_parser
from tests import mock_http_bundle


class TestSingleImageParser(unittest.IsolatedAsyncioTestCase):

    async def test_recognizes_image(self):
        bundle = mock_http_bundle(
            lambda request: httpx.Response(200, headers={"Content-Type": "image/jpeg"})
        )
        result = await single_image_parser("https://example.com/image.jpg", bundle)
        self.assertEqual(result, ["https://example.com/image.jpg"])

    async def test_follows_redirects_to_final_url(self):
        # httpx doesn't follow redirects by default, so this used to return []
        def handler(request):
            if request.url.path == "/short":
                return httpx.Response(
                    302, headers={"Location": "https://cdn.example.com/full.png"}
                )
            return httpx.Response(200, headers={"Content-Type": "image/png"})

        result = await single_image_parser(
            "https://example.com/short", mock_http_bundle(handler)
        )
        self.assertEqual(result, ["https://cdn.example.com/full.png"])

    async def test_does_not_read_body(self):
        # the image is downloaded later; reading it here would fetch it twice
        class Body(httpx.AsyncByteStream):
            read = False

            async def __aiter__(self):
                Body.read = True
                yield b"x" * 1024

        bundle = mock_http_bundle(
            lambda request: httpx.Response(
                200, headers={"Content-Type": "image/png"}, stream=Body()
            )
        )
        await single_image_parser("https://example.com/a.png", bundle)
        self.assertFalse(Body.read)

    async def test_rejects_non_images_and_errors(self):
        for status, content_type in [
            (200, "text/html; charset=utf-8"),
            (404, "image/png"),
            (200, None),
        ]:
            with self.subTest(status=status, content_type=content_type):
                headers = {"Content-Type": content_type} if content_type else {}
                bundle = mock_http_bundle(
                    lambda request, s=status, h=headers: httpx.Response(s, headers=h)
                )
                self.assertEqual(
                    await single_image_parser("https://example.com/page", bundle), []
                )


class TestFindUrls(unittest.IsolatedAsyncioTestCase):

    async def test_combines_parsers_in_order_without_duplicates(self):
        async def parser_one(url, clients):
            return ["c", "a"]

        async def parser_two(url, clients):
            return ["a", "b"]

        result = await find_urls(
            "https://example.com", None, parsers=[parser_one, parser_two]
        )
        self.assertEqual(result, ["c", "a", "b"])

    async def test_failing_parser_does_not_discard_others(self):
        # one parser raising used to fail the whole post through gather
        async def broken(url, clients):
            raise KeyError("sizes")

        async def working(url, clients):
            return ["a"]

        result = await find_urls("https://example.com", None, parsers=[broken, working])
        self.assertEqual(result, ["a"])


if __name__ == "__main__":
    unittest.main()
