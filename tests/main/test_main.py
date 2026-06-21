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
        self.assertEqual(builder.add_subreddit.call_count, 2)
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

    async def test_swallows_errors_and_logs(self):
        # a raising submission must NOT propagate (it would abort the TaskGroup)
        wrapped = _fake_wrapped("T", "pics")
        wrapped.find_urls = AsyncMock(side_effect=RuntimeError("boom"))
        file_manager = MagicMock()
        file_manager.save_files = AsyncMock(return_value=[])
        file_manager.log = AsyncMock()

        result = await process_submission(
            wrapped,
            MagicMock(),
            file_manager,
            asyncio.Semaphore(1),
            asyncio.Semaphore(1),
            log=True,
        )

        self.assertEqual(result, [])
        wrapped.log_record.assert_called_once_with(exception="boom")
        file_manager.log.assert_awaited_once()
        wrapped.unsave.assert_not_awaited()

    async def test_error_without_log_is_silent(self):
        wrapped = _fake_wrapped("T", "pics")
        wrapped.find_urls = AsyncMock(side_effect=RuntimeError("boom"))
        file_manager = MagicMock()
        file_manager.log = AsyncMock()

        result = await process_submission(
            wrapped,
            MagicMock(),
            file_manager,
            asyncio.Semaphore(1),
            asyncio.Semaphore(1),
            log=False,
        )

        self.assertEqual(result, [])
        file_manager.log.assert_not_awaited()


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


class TestMain(unittest.IsolatedAsyncioTestCase):

    async def test_runs_pipeline_and_collects_results(self):
        with tempfile.TemporaryDirectory() as directory:
            args = _args(directory=directory, log=True)
            # one submission yields a file, one yields nothing
            w1 = _fake_wrapped("Alpha", downloads=[(b"a", "jpg")])
            w2 = _fake_wrapped("Beta", downloads=[])

            async def fake_build_stream(_clients, **_kwargs):
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
            # one progress line (w1 saved a file; w2 didn't) + the final summary
            self.assertEqual(mock_print.call_count, 2)
            summary = mock_print.call_args_list[-1].args[0]
            self.assertIn("1 file(s)", summary)
            self.assertIn("2 submission(s)", summary)
