import unittest
from unittest.mock import AsyncMock, patch

from core.parsers.parsers import find_urls, single_image_parser


class TestParsers(unittest.IsolatedAsyncioTestCase):
    async def test_single_image_parser(self):
        mock_client = AsyncMock()
        response = AsyncMock()
        response.status_code = 200
        response.headers = {"Content-type": "image/jpeg"}
        response.url = "https://example.com/image.jpg"
        mock_client.get.return_value = response

        result = await single_image_parser("https://example.com/image.jpg", mock_client)

        self.assertEqual(result, {"https://example.com/image.jpg"})

    async def test_find_urls(self):
        async def parser_one(url, client):
            return {"a"}

        async def parser_two(url, client):
            return {"b"}

        mock_client = AsyncMock()

        with patch("core.parsers.parsers.PARSERS", {parser_one, parser_two}):
            result = await find_urls("https://example.com", mock_client)

        self.assertEqual(result, {"a", "b"})


if __name__ == "__main__":
    unittest.main()
