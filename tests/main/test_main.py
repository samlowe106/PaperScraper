import asyncio
import tempfile
import unittest
from argparse import Namespace
from unittest.mock import AsyncMock, MagicMock, patch

from src.main import build_stream, main, process_download, process_submission
from src.reddit import SortOption
from tests import async_iter


def _fake_wrapped(title, subreddit="pics", downloads=None):
    """A stand-in for SubmissionWrapper with async find_urls/download."""
    wrapped = MagicMock()
    wrapped.title = title
    wrapped.subreddit = subreddit
    wrapped.find_urls = AsyncMock()
    wrapped.download = AsyncMock(return_value=downloads or [])
    return wrapped


class TestBuildStream(unittest.IsolatedAsyncioTestCase):

    async def test_no_saved_adds_each_subreddit(self):
        args = Namespace(
            saved=False, subreddit=["pics", "r/art"], sortby=SortOption.HOT
        )
        clients = MagicMock()
        with patch("src.main.StreamBuilder") as MockBuilder:
            builder = MockBuilder.return_value
            result = await build_stream(args, clients)
        builder.set_redditor.assert_not_called()
        self.assertEqual(builder.add_subreddit.call_count, 2)
        builder.build.assert_called_once_with(clients)
        self.assertEqual(result, builder.build.return_value)

    async def test_saved_prompts_for_credentials(self):
        args = Namespace(saved=True, subreddit=[], sortby=SortOption.HOT)
        clients = MagicMock()
        with (
            patch("src.main.StreamBuilder") as MockBuilder,
            patch("builtins.input", return_value="user"),
            patch("src.main.getpass", return_value="pw"),
        ):
            builder = MockBuilder.return_value
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


class TestMain(unittest.IsolatedAsyncioTestCase):

    async def test_runs_pipeline_and_collects_results(self):
        with tempfile.TemporaryDirectory() as directory:
            args = Namespace(
                directory=directory,
                organize=False,
                saved=False,
                subreddit=[],
                sortby=SortOption.HOT,
            )
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
