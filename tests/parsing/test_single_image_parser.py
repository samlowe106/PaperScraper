import unittest
from unittest.mock import MagicMock

import httpx
import pytest

from src.parsing import single_image_parser


class TestSingleImageParser(unittest.IsolatedAsyncioTestCase):

    @pytest.mark.vcr
    async def test_recognizes_single_image(self):
        mock_client_bundle = MagicMock()
        mock_client_bundle.http = httpx.AsyncClient()
        # Mushroom Generator by beeple
        result = await single_image_parser(
            "https://cdna.artstation.com/p/assets/images/images/012/127/414/large/beeple-07-25-18.jpg?1533161904",
            mock_client_bundle,
        )

        self.assertEqual(
            result,
            {
                "https://cdna.artstation.com/p/assets/images/images/012/127/414/large/beeple-07-25-18.jpg?1533161904"
            },
        )

    @pytest.mark.vcr
    async def test_png(self):
        # Early Summer Holiday by 六七質
        mock_client_bundle = MagicMock()
        mock_client_bundle.http = httpx.AsyncClient()

        result = await single_image_parser(
            "https://i.redd.it/1u3xx7t7tmra1.png", mock_client_bundle
        )

        self.assertEqual(result, {"https://i.redd.it/1u3xx7t7tmra1.png"})

    @pytest.mark.vcr
    async def test_does_not_recognizes_other(self):
        mock_client_bundle = MagicMock()
        mock_client_bundle.http = httpx.AsyncClient()
        result = await single_image_parser(
            "https://google.com",
            mock_client_bundle,
        )

        self.assertEqual(result, set())

        result = await single_image_parser(
            "https://youtu.be/dQw4w9WgXcQ",
            mock_client_bundle,
        )

        self.assertEqual(result, set())
