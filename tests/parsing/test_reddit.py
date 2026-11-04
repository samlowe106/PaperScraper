import json
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from asyncpraw.models import Submission

from src.core import AsyncClientBundle
from src.parsing import reddit_parser


class TestRedditParser(unittest.IsolatedAsyncioTestCase):
    """Replays real recorded reddit API responses (VCR cassettes)"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        with open("tests/parsing/reddit_test_data.json") as f:
            self.json_data = json.load(f)

    @pytest.mark.vcr()
    async def test_single_image(self):
        case = self.json_data["single_image"][0]
        async with AsyncClientBundle() as client_bundle:
            client_bundle.set_reddit()

            actual = await reddit_parser(case["url"], client_bundle)
            self.assertEqual(actual, case["expected"])

    @pytest.mark.vcr()
    async def test_gallery(self):
        case = self.json_data["gallery"][0]
        async with AsyncClientBundle() as client_bundle:
            client_bundle.set_reddit()

            actual = await reddit_parser(case["url"], client_bundle)
            # in gallery order: album files are numbered by position
            self.assertEqual(actual, case["expected"])


class _FakeReddit:
    """
    Stands in for asyncpraw.Reddit. Like the real one, submission() rejects urls
    that aren't submissions (using asyncpraw's own parsing) before fetching.
    """

    def __init__(self, submission=None):
        self.submission_obj = submission
        self.fetched: list[str] = []

    async def submission(self, url):
        Submission.id_from_url(url)  # raises InvalidURL like the real call
        self.fetched.append(url)
        return self.submission_obj


def _bundle(submission=None):
    bundle = MagicMock()
    bundle.reddit = _FakeReddit(submission)
    return bundle


def _gallery_submission(items: list[tuple[str, dict]]):
    # SimpleNamespace, unlike Mock, raises AttributeError for missing fields,
    # just as a fetched asyncpraw Submission does
    return SimpleNamespace(
        url="https://www.reddit.com/gallery/abc123",
        is_gallery=True,
        gallery_data={"items": [{"media_id": media_id} for media_id, _ in items]},
        media_metadata=dict(items),
    )


class TestRedditParserOffline(unittest.IsolatedAsyncioTestCase):

    async def test_non_reddit_urls_are_not_fetched(self):
        # these used to be read as submission ids ("XyZ9") and fetched, or raise
        # InvalidURL and fail the post
        bundle = _bundle()
        for url in [
            "https://imgur.com/a/XyZ9",
            "https://i.imgur.com/AbC12",
            "https://www.flickr.com/photos/u/12345/",
            "https://example.com/abc",
        ]:
            with self.subTest(url):
                self.assertEqual(await reddit_parser(url, bundle), [])
        self.assertEqual(bundle.reddit.fetched, [])

    async def test_direct_reddit_image_needs_no_fetch(self):
        bundle = _bundle()
        url = "https://i.redd.it/abc123.jpg"
        self.assertEqual(await reddit_parser(url, bundle), [url])
        self.assertEqual(bundle.reddit.fetched, [])

    async def test_media_wrapper_url(self):
        bundle = _bundle()
        with open("tests/parsing/reddit_test_data.json") as f:
            case = json.load(f)["single_image"][1]
        self.assertEqual(await reddit_parser(case["url"], bundle), case["expected"])
        self.assertEqual(bundle.reddit.fetched, [])

    async def test_non_submission_reddit_url(self):
        bundle = _bundle()
        url = "https://www.reddit.com/r/pics/"
        self.assertEqual(await reddit_parser(url, bundle), [])

    async def test_relative_crosspost_url(self):
        submission = SimpleNamespace(url="https://i.redd.it/parent.jpg")
        bundle = _bundle(submission)
        result = await reddit_parser("/r/pics/comments/abc123/title/", bundle)
        self.assertEqual(result, ["https://i.redd.it/parent.jpg"])
        self.assertEqual(
            bundle.reddit.fetched,
            ["https://www.reddit.com/r/pics/comments/abc123/title/"],
        )

    async def test_link_post_without_is_gallery(self):
        # non-gallery submissions have no is_gallery attribute; reading it used
        # to raise AttributeError
        submission = SimpleNamespace(url="https://www.reddit.com/r/x/comments/abc/t/")
        result = await reddit_parser(submission.url, _bundle(submission))
        self.assertEqual(result, [])

    async def test_gallery_keeps_order_and_handles_animated_and_failed_items(self):
        submission = _gallery_submission(
            [
                ("c", {"status": "valid", "s": {"u": "https://p/c.jpg?a=1&amp;b=2"}}),
                # animated items have gif/mp4 instead of u; used to raise KeyError
                ("a", {"status": "valid", "s": {"gif": "https://p/a.gif"}}),
                ("v", {"status": "valid", "s": {"mp4": "https://p/v.mp4"}}),
                # failed/deleted items have no source; used to raise KeyError
                ("x", {"status": "failed"}),
                ("b", {"status": "valid", "s": {"u": "https://p/b.jpg"}}),
            ]
        )
        result = await reddit_parser(submission.url, _bundle(submission))
        self.assertEqual(
            result,
            [
                "https://p/c.jpg?a=1&b=2",
                "https://p/a.gif",
                "https://p/v.mp4",
                "https://p/b.jpg",
            ],
        )

    async def test_gallery_item_missing_from_metadata(self):
        submission = _gallery_submission(
            [("a", {"status": "valid", "s": {"u": "https://p/a.jpg"}})]
        )
        submission.gallery_data["items"].append({"media_id": "gone"})
        result = await reddit_parser(submission.url, _bundle(submission))
        self.assertEqual(result, ["https://p/a.jpg"])
