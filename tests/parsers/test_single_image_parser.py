import unittest
from unittest.mock import AsyncMock

import httpx
import pytest

from src.parsers import single_image_parser
from src.parsers.single_image import get_response_file_extension


class TestSingleImageParser(unittest.IsolatedAsyncioTestCase):

    async def test_recognizes_single_image(self):
        mock_client = AsyncMock()
        response = AsyncMock()
        response.status_code = 200
        response.headers = {"Content-type": "image/jpeg"}
        response.url = "https://example.com/image.jpg"
        mock_client.get.return_value = response

        result = await single_image_parser("https://example.com/image.jpg", mock_client)

        self.assertEqual(result, {"https://example.com/image.jpg"})

    async def test_does_not_recognizes_other(self):
        mock_client = AsyncMock()
        response = AsyncMock()
        response.status_code = 200
        response.headers = {"Content-type": "text/html"}
        response.url = "https://example.com/"
        mock_client.get.return_value = response

        result = await single_image_parser("https://example.com/", mock_client)

        self.assertEqual(result, set())


class TestGetExtension(unittest.TestCase):

    @pytest.mark.vcr
    def test_jpeg(self):
        # Mushroom Generator by beeple
        r = httpx.get(
            "https://cdna.artstation.com/p/assets/images/images/012/127/414/large/beeple-07-25-18.jpg?1533161904"
        )
        self.assertEqual(get_response_file_extension(r), ".jpeg")

    @pytest.mark.vcr
    def test_png(self):
        # Early Summer Holiday by 六七質
        r = httpx.get("https://i.redd.it/1u3xx7t7tmra1.png")
        self.assertEqual(get_response_file_extension(r), ".png")

    # TODO: test other formats like .gif and .webp
