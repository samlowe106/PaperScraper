import asyncio
import tempfile
import time
import unittest
from argparse import Namespace
from unittest.mock import AsyncMock, MagicMock, patch

from src.main import (
    build_predicate,
    build_stream,
    main,
    max_age_seconds,
    process_download,
    process_submission,
)
from src.reddit import SortOption
from tests import async_iter


def _args(**overrides):
    """A Namespace with all fields main()/build_stream() read, overridable."""
    defaults = dict(
        directory="Output",
        organize=False,
        saved=False,
        subreddit=[],
        sortby=SortOption.HOT,
        limit=10,
        karma=None,
        hours=None,
        days=None,
        years=None,
        log=False,
        unsave=False,
    )
    defaults.update(overrides)
    return Namespace(**defaults)


def _fake_wrapped(title, subreddit="pics", downloads=None):
    """A stand-in for SubmissionWrapper with async find_urls/download/unsave."""
    wrapped = MagicMock()
    wrapped.title = title
    wrapped.subreddit = subreddit
    wrapped.find_urls = AsyncMock()
    wrapped.download = AsyncMock(return_value=downloads or [])
    wrapped.unsave = AsyncMock()
    wrapped.log_record = MagicMock(
        return_value={"title": title, "recognized_urls": [], "exception": ""}
    )
    return wrapped


class TestBuildStream(unittest.IsolatedAsyncioTestCase):

    async def test_no_saved_adds_each_subreddit(self):
        args = _args(subreddit=["pics", "r/art"])
        clients = MagicMock()
        with patch("src.main.StreamBuilder") as MockBuilder:
            builder = MockBuilder.return_value
            builder.build = AsyncMock()  # build() is awaited
            result = await build_stream(args, clients)
        builder.set_redditor.assert_not_called()
        self.assertEqual(builder.add_subreddit.call_count, 2)
        builder.build.assert_awaited_once_with(clients)
        self.assertEqual(result, builder.build.return_value)

    async def test_saved_prompts_for_credentials(self):
        args = _args(saved=True)
        clients = MagicMock()
        with (
            patch("src.main.StreamBuilder") as MockBuilder,
            patch("builtins.input", return_value="user"),
            patch("src.main.getpass", return_value="pw"),
        ):
            builder = MockBuilder.return_value
            builder.build = AsyncMock()  # build() is awaited
            await build_stream(args, clients)
        builder.set_redditor.assert_called_once_with("user", "pw")
        builder.add_subreddit.assert_not_called()


class TestProcessDownload(unittest.IsolatedAsyncioTestCase):

    async def test_saves_downloaded_files(self):
        wrapped = _fake_wrapped("T", "pics", downloads=[(b"x", "jpg")])
        file_manager = MagicMock()
        file_manager.save_files = AsyncMock(return_value=["/out/T.jpg"])
        client = MagicMock()

        result = await process_download(
            wrapped, client, file_manager, asyncio.Semaphore(1)
        )

        wrapped.download.assert_awaited_once_with(client)
        file_manager.save_files.assert_awaited_once_with(
            "T", [(b"x", "jpg")], subreddit="pics"
        )
        self.assertEqual(result, ["/out/T.jpg"])


class TestProcessSubmission(unittest.IsolatedAsyncioTestCase):

    async def test_finds_urls_with_bundle_then_downloads_with_http(self):
        wrapped = _fake_wrapped("T", "pics", downloads=[(b"x", "jpg")])
        clients = MagicMock()
        file_manager = MagicMock()
        file_manager.save_files = AsyncMock(return_value=["/out/T.jpg"])

        result = await process_submission(
            wrapped, clients, file_manager, asyncio.Semaphore(1), asyncio.Semaphore(1)
        )

        # find_urls gets the whole bundle; download gets just the http client
        wrapped.find_urls.assert_awaited_once_with(clients)
        wrapped.download.assert_awaited_once_with(clients.http)
        self.assertEqual(result, ["/out/T.jpg"])

    async def _run(self, *, saved_paths, log=False, unsave=False):
        wrapped = _fake_wrapped("T", "pics", downloads=[(b"x", "jpg")])
        clients = MagicMock()
        file_manager = MagicMock()
        file_manager.save_files = AsyncMock(return_value=saved_paths)
        file_manager.log = AsyncMock()
        await process_submission(
            wrapped,
            clients,
            file_manager,
            asyncio.Semaphore(1),
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


class TestMaxAgeSeconds(unittest.TestCase):

    def test_none_when_no_age_given(self):
        self.assertIsNone(max_age_seconds(_args()))

    def test_hours(self):
        self.assertEqual(max_age_seconds(_args(hours=2)), 2 * 3600)

    def test_days(self):
        self.assertEqual(max_age_seconds(_args(days=3)), 3 * 86400)

    def test_years(self):
        self.assertEqual(max_age_seconds(_args(years=1)), 365 * 86400)


class TestBuildPredicate(unittest.TestCase):

    @staticmethod
    def _wrapped(score=0, age_seconds=0.0):
        wrapped = MagicMock()
        wrapped.score = score
        wrapped.created_utc = time.time() - age_seconds
        return wrapped

    def test_no_filters_keeps_everything(self):
        predicate = build_predicate(_args())
        self.assertTrue(predicate(self._wrapped(score=-100, age_seconds=10 * 86400)))

    def test_karma_filters_low_scores(self):
        predicate = build_predicate(_args(karma=50))
        self.assertTrue(predicate(self._wrapped(score=50)))
        self.assertFalse(predicate(self._wrapped(score=49)))

    def test_age_filters_old_posts(self):
        predicate = build_predicate(_args(days=7))
        self.assertTrue(predicate(self._wrapped(age_seconds=86400)))  # 1 day old
        self.assertFalse(predicate(self._wrapped(age_seconds=10 * 86400)))  # 10 days

    def test_karma_and_age_combined(self):
        predicate = build_predicate(_args(karma=10, hours=24))
        self.assertTrue(predicate(self._wrapped(score=10, age_seconds=3600)))
        self.assertFalse(predicate(self._wrapped(score=10, age_seconds=2 * 86400)))
        self.assertFalse(predicate(self._wrapped(score=5, age_seconds=3600)))


class TestMain(unittest.IsolatedAsyncioTestCase):

    async def test_runs_pipeline_and_collects_results(self):
        with tempfile.TemporaryDirectory() as directory:
            args = _args(directory=directory, log=True)
            # one submission yields a file, one yields nothing
            w1 = _fake_wrapped("Alpha", downloads=[(b"a", "jpg")])
            w2 = _fake_wrapped("Beta", downloads=[])

            async def fake_build_stream(_args, _clients):
                return async_iter([w1, w2])

            with (
                patch("src.main.build_stream", side_effect=fake_build_stream),
                patch("builtins.print") as mock_print,
            ):
                await main(args)

            # every submission is processed (real process_submission/_download +
            # a real file_manager writing into the temp dir)
            w1.find_urls.assert_awaited_once()
            w2.find_urls.assert_awaited_once()
            w1.download.assert_awaited_once()
            w2.download.assert_awaited_once()
            # only w1 produced a saved file, so exactly one result is printed
            self.assertEqual(mock_print.call_count, 1)
