import json
import unittest

import pytest

from src.core import AsyncClientBundle
from src.parsing import reddit_parser


class TestRedditParser(unittest.IsolatedAsyncioTestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        with open("tests/parsing/reddit_test_data.json") as f:
            json_data = json.load(f)

        self.single_image_url = json_data["single_image"][0]["url"]
        self.single_image_expected = set(json_data["single_image"][0]["expected"])
        self.gallery_url = json_data["gallery"][0]["url"]
        self.gallery_expected = set(json_data["gallery"][0]["expected"])

    @pytest.mark.vcr()
    async def test_single_image(self):

        async with AsyncClientBundle() as client_bundle:
            client_bundle.set_reddit()

            actual = await reddit_parser(self.single_image_url, client_bundle)
            self.assertSetEqual(self.single_image_expected, actual)

    @pytest.mark.vcr()
    async def test_gallery(self):
        async with AsyncClientBundle() as client_bundle:
            client_bundle.set_reddit()

            actual = await reddit_parser(self.gallery_url, client_bundle)
            self.assertSetEqual(self.gallery_expected, actual)
