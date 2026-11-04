import asyncio
import json
import os
import tempfile
import time
import unittest
from argparse import Namespace
from unittest.mock import AsyncMock, MagicMock, call, patch

import httpx

from src.core import make_http_client
from src.main import (
    build_predicate,
    build_stream,
    main,
    max_age_seconds,
    process_submission,
)
from src.reddit import SortOption, SubmissionWrapper
from tests import SubmissionMockFactory, async_iter


def _args(**overrides):
    """A Namespace with all fields main()/build_stream() read, overridable."""
    defaults = {
        "directory": "Output",
        "organize": False,
        "saved": False,
        "subreddit": [],
        "sortby": SortOption.HOT,
        "limit": 10,
        "karma": None,
        "hours": None,
        "days": None,
        "years": None,
        "log": False,
        "unsave": False,
    }
    defaults.update(overrides)
    return Namespace(**defaults)


def _fake_wrapped(title, subreddit="pics", saved=None):
    """
    A stand-in for SubmissionWrapper with async find_urls/download/unsave;
    download "saves" the given paths
    """
    wrapped = MagicMock()
    wrapped.title = title
    wrapped.subreddit = subreddit
    wrapped.find_urls = AsyncMock()
    wrapped.download = AsyncMock(return_value=saved or [])
    wrapped.unsave = AsyncMock()
    wrapped.log_record = MagicMock(
        return_value={"title": title, "recognized_urls": [], "exception": ""}
    )
    return wrapped


class TestBuildStream(unittest.IsolatedAsyncioTestCase):

    async def test_no_saved_adds_each_subreddit(self):
        clients = MagicMock()
        with patch("src.main.StreamBuilder") as MockBuilder:
            builder = MockBuilder.return_value
            builder.build = AsyncMock()  # build() is awaited
            result = await build_stream(
                clients,
                saved=False,
                subreddits=["pics", "r/art"],
                sortby=SortOption.HOT,
                limit=10,
                predicate=lambda _: True,
            )
        builder.set_redditor.assert_not_called()
        self.assertEqual(
            builder.add_subreddit.call_args_list,
            [call("pics", SortOption.HOT), call("r/art", SortOption.HOT)],
        )
        builder.build.assert_awaited_once_with(clients)
        self.assertEqual(result, builder.build.return_value)

    async def test_saved_prompts_for_credentials(self):
        clients = MagicMock()
        with (
            patch("src.main.StreamBuilder") as MockBuilder,
            patch("builtins.input", return_value="user"),
            patch("src.main.getpass", return_value="pw"),
        ):
            builder = MockBuilder.return_value
            builder.build = AsyncMock()  # build() is awaited
            await build_stream(
                clients,
                saved=True,
                subreddits=[],
                sortby=SortOption.HOT,
                limit=10,
                predicate=lambda _: True,
            )
        builder.set_redditor.assert_called_once_with("user", "pw")
        builder.add_subreddit.assert_not_called()


class TestProcessSubmission(unittest.IsolatedAsyncioTestCase):

    async def test_finds_urls_with_bundle_then_downloads_with_http(self):
        wrapped = _fake_wrapped("T", "pics", saved=["/out/T.jpg"])
        clients = MagicMock()
        file_manager = MagicMock()

        result = await process_submission(
            wrapped, clients, file_manager, asyncio.Semaphore(1)
        )

        # find_urls gets the whole bundle; download gets just the http client
        wrapped.find_urls.assert_awaited_once_with(clients)
        wrapped.download.assert_awaited_once_with(clients.http, file_manager)
        self.assertEqual(result, ["/out/T.jpg"])

    async def _run(self, *, saved_paths, log=False, unsave=False):
        wrapped = _fake_wrapped("T", "pics", saved=saved_paths)
        clients = MagicMock()
        file_manager = MagicMock()
        file_manager.log = AsyncMock()
        await process_submission(
            wrapped,
            clients,
            file_manager,
            asyncio.Semaphore(1),
            log=log,
            unsave=unsave,
        )
        return wrapped, file_manager

    async def test_unsave_when_enabled_and_something_saved(self):
        wrapped, _ = await self._run(saved_paths=["/out/T.jpg"], unsave=True)
        wrapped.unsave.assert_awaited_once()

    async def test_no_unsave_when_nothing_saved(self):
        # opt-in unsave must not fire when the download produced no files
        wrapped, _ = await self._run(saved_paths=[], unsave=True)
        wrapped.unsave.assert_not_awaited()

    async def test_no_unsave_by_default(self):
        wrapped, _ = await self._run(saved_paths=["/out/T.jpg"], unsave=False)
        wrapped.unsave.assert_not_awaited()

    async def test_logs_via_file_manager_when_enabled(self):
        wrapped, file_manager = await self._run(saved_paths=["/out/T.jpg"], log=True)
        file_manager.log.assert_awaited_once_with(wrapped.log_record.return_value)

    async def test_no_log_when_disabled(self):
        _, file_manager = await self._run(saved_paths=["/out/T.jpg"], log=False)
        file_manager.log.assert_not_awaited()

    async def test_swallows_errors_and_logs(self):
        # a raising submission must NOT propagate (it would abort the TaskGroup)
        wrapped = _fake_wrapped("T", "pics")
        wrapped.find_urls = AsyncMock(side_effect=RuntimeError("boom"))
        file_manager = MagicMock()
        file_manager.log = AsyncMock()

        result = await process_submission(
            wrapped,
            MagicMock(),
            file_manager,
            asyncio.Semaphore(1),
            log=True,
        )

        self.assertEqual(result, [])
        wrapped.log_record.assert_called_once_with(exception="boom")
        file_manager.log.assert_awaited_once()
        wrapped.unsave.assert_not_awaited()

    async def test_failing_log_does_not_escape(self):
        # process_submission runs in a TaskGroup; anything it raises cancels
        # every other submission
        wrapped = _fake_wrapped("T", "pics", saved=["/out/T.jpg"])
        file_manager = MagicMock()
        file_manager.log = AsyncMock(side_effect=OSError("disk full"))

        result = await process_submission(
            wrapped,
            MagicMock(),
            file_manager,
            asyncio.Semaphore(1),
            log=True,
        )

        self.assertEqual(result, [])
        self.assertEqual(file_manager.log.await_count, 2)

    async def test_error_without_log_writes_no_log(self):
        wrapped = _fake_wrapped("T", "pics")
        wrapped.find_urls = AsyncMock(side_effect=RuntimeError("boom"))
        file_manager = MagicMock()
        file_manager.log = AsyncMock()

        result = await process_submission(
            wrapped,
            MagicMock(),
            file_manager,
            asyncio.Semaphore(1),
            log=False,
        )

        self.assertEqual(result, [])
        file_manager.log.assert_not_awaited()


class TestMainPipeline(unittest.IsolatedAsyncioTestCase):
    """
    Runs the real main(): real client bundle, wrappers, parsers, downloads and
    file manager. Only the network (a mock transport) and reddit's listing
    (build_stream) are faked.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.requests: list[str] = []

    async def _handler(self, request):
        self.requests.append(str(request.url))
        # every request yields to the loop first, like a real network call
        await asyncio.sleep(0)
        host, path = request.url.host, request.url.path
        if host in ("i.redd.it", "preview.redd.it"):
            return httpx.Response(
                200, headers={"Content-Type": "image/jpeg"}, content=path.encode()
            )
        if host == "short.example" and path == "/img":
            return httpx.Response(
                302, headers={"Location": "https://cdn.example/full.png"}
            )
        if host == "cdn.example":
            return httpx.Response(
                200, headers={"Content-Type": "image/png"}, content=b"png"
            )
        if host == "api.imgur.com" and path == "/3/album/AbC/images":
            links = [f"https://i.imgur.com/{n}.png" for n in ("z", "a", "m")]
            return httpx.Response(200, json={"data": [{"link": u} for u in links]})
        if host == "i.imgur.com":
            return httpx.Response(
                200, headers={"Content-Type": "image/png"}, content=path.encode()
            )
        return httpx.Response(404, headers={"Content-Type": "text/html"})

    async def _run(self, submissions, handler=None, **args):
        stream_args = {}

        async def fake_build_stream(clients, **kwargs):
            stream_args["clients"] = clients
            return async_iter(SubmissionWrapper(s) for s in submissions)

        transport = httpx.MockTransport(handler or self._handler)
        with (
            patch("src.main.build_stream", side_effect=fake_build_stream),
            patch(
                "src.core.client_bundle.make_http_client",
                lambda: make_http_client(transport=transport),
            ),
            patch("builtins.print") as mock_print,
        ):
            await main(_args(directory=self._tmp.name, **args))

        (output,) = os.listdir(self._tmp.name)
        self.output = os.path.join(self._tmp.name, output)
        self.printed = [call.args[0] for call in mock_print.call_args_list]
        return stream_args["clients"]

    def _files(self):
        found = {}
        for root, _, files in os.walk(self.output):
            for name in files:
                path = os.path.join(root, name)
                with open(path, "rb") as f:
                    found[os.path.relpath(path, self.output)] = f.read()
        return found

    async def test_downloads_every_kind_of_post(self):
        await self._run(
            [
                SubmissionMockFactory(
                    title="Direct", url="https://i.redd.it/one.jpg", subreddit="pics"
                ),
                SubmissionMockFactory(
                    title="Redirected", url="https://short.example/img", subreddit="art"
                ),
                SubmissionMockFactory(
                    title="Album", url="https://imgur.com/a/AbC", subreddit="pics"
                ),
                SubmissionMockFactory(
                    title="Text post",
                    url="https://example.com/nothing",
                    subreddit="pics",
                ),
            ],
            organize=True,
        )

        # exact paths: no "..jpg", albums inside the subreddit folder (not a
        # nested copy of the output path), album files in album order
        self.assertEqual(
            self._files(),
            {
                os.path.join("pics", "Direct.jpg"): b"/one.jpg",
                os.path.join("art", "Redirected.png"): b"png",
                os.path.join("pics", "Album", "0.png"): b"/z.png",
                os.path.join("pics", "Album", "1.png"): b"/a.png",
                os.path.join("pics", "Album", "2.png"): b"/m.png",
            },
        )
        self.assertIn("Done -- saved 5 file(s) from 4 submission(s).", self.printed)
        # no parser blew up on a url meant for another parser
        self.assertFalse([line for line in self.printed if "failed" in line])

    async def test_gallery_needs_no_reddit_fetch(self):
        # build_stream is faked, so clients.reddit is never set up: fetching the
        # post would fail the reddit parser
        gallery = SubmissionMockFactory(
            title="Gallery",
            url="https://www.reddit.com/gallery/abc",
            is_gallery=True,
            gallery_data={"items": [{"media_id": "y"}, {"media_id": "x"}]},
            media_metadata={
                media_id: {
                    "status": "valid",
                    "s": {"u": f"https://preview.redd.it/{media_id}.jpg?a=1&amp;b=2"},
                }
                for media_id in "xy"
            },
        )
        await self._run([gallery])
        self.assertEqual(
            self._files(),
            {
                os.path.join("Gallery", "0.jpg"): b"/y.jpg",
                os.path.join("Gallery", "1.jpg"): b"/x.jpg",
            },
        )
        self.assertEqual(
            self.requests,
            [
                "https://preview.redd.it/y.jpg?a=1&b=2",
                "https://preview.redd.it/x.jpg?a=1&b=2",
            ],
        )
        self.assertFalse([line for line in self.printed if "failed" in line])

    async def test_clients_stay_open_until_every_submission_finishes(self):
        # the bundle used to close as soon as the stream ran out, while every
        # submission task was still pending
        clients = await self._run(
            [
                SubmissionMockFactory(
                    title=f"Post {i}", url=f"https://i.redd.it/{i}.jpg"
                )
                for i in range(5)
            ]
        )
        self.assertEqual(len(self._files()), 5)
        self.assertTrue(clients.http.is_closed)

    async def test_active_posts_are_limited(self):
        # each post's requests share its image path, so distinct paths in flight
        # at once are the posts being worked on
        in_flight: set[str] = set()
        peak = 0

        async def tracking(request):
            nonlocal peak
            in_flight.add(request.url.path)
            peak = max(peak, len(in_flight))
            await asyncio.sleep(0.02)
            in_flight.discard(request.url.path)
            return await self._handler(request)

        with patch("src.main.MAX_ACTIVE_POSTS", 2):
            await self._run(
                [
                    SubmissionMockFactory(
                        title=f"Post {i}", url=f"https://i.redd.it/{i}.jpg"
                    )
                    for i in range(6)
                ],
                handler=tracking,
            )
        self.assertEqual(peak, 2)
        self.assertEqual(len(self._files()), 6)

    async def test_same_titles_dont_overwrite(self):
        await self._run(
            [
                SubmissionMockFactory(title="Same", url=f"https://i.redd.it/{i}.jpg")
                for i in range(3)
            ]
        )
        self.assertEqual(
            sorted(self._files().values()), [b"/0.jpg", b"/1.jpg", b"/2.jpg"]
        )

    async def test_log_records_each_post(self):
        await self._run(
            [SubmissionMockFactory(title="Direct", url="https://i.redd.it/one.jpg")],
            log=True,
        )
        with open(os.path.join(self.output, "log.txt"), encoding="utf-8") as f:
            (record,) = [json.loads(line) for line in f]
        self.assertEqual(record["recognized_urls"], ["https://i.redd.it/one.jpg"])
        self.assertEqual(record["exception"], "")


class TestMaxAgeSeconds(unittest.TestCase):

    def test_none_when_no_age_given(self):
        self.assertIsNone(max_age_seconds(None, None, None))

    def test_hours(self):
        self.assertEqual(max_age_seconds(2, None, None), 2 * 3600)

    def test_days(self):
        self.assertEqual(max_age_seconds(None, 3, None), 3 * 86400)

    def test_years(self):
        self.assertEqual(max_age_seconds(None, None, 1), 365 * 86400)


class TestBuildPredicate(unittest.TestCase):

    @staticmethod
    def _wrapped(score=0, age_seconds=0.0):
        wrapped = MagicMock()
        wrapped.score = score
        wrapped.created_utc = time.time() - age_seconds
        return wrapped

    def test_no_filters_keeps_everything(self):
        predicate = build_predicate(None, None)
        self.assertTrue(predicate(self._wrapped(score=-100, age_seconds=10 * 86400)))

    def test_karma_filters_low_scores(self):
        predicate = build_predicate(50, None)
        self.assertTrue(predicate(self._wrapped(score=50)))
        self.assertFalse(predicate(self._wrapped(score=49)))

    def test_age_filters_old_posts(self):
        predicate = build_predicate(None, 7 * 86400)  # 7 days
        self.assertTrue(predicate(self._wrapped(age_seconds=86400)))  # 1 day old
        self.assertFalse(predicate(self._wrapped(age_seconds=10 * 86400)))  # 10 days

    def test_karma_and_age_combined(self):
        predicate = build_predicate(10, 24 * 3600)  # score >= 10, <= 24h old
        self.assertTrue(predicate(self._wrapped(score=10, age_seconds=3600)))
        self.assertFalse(predicate(self._wrapped(score=10, age_seconds=2 * 86400)))
        self.assertFalse(predicate(self._wrapped(score=5, age_seconds=3600)))
