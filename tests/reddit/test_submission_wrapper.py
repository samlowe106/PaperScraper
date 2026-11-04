import asyncio
import io
import os
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

import httpx

from src.core import UniqueDirectoryFileManager
from src.reddit.submission_wrapper import _download_to_file
from tests import SubmissionWrapperFactory, mock_http_bundle

# Note: log() and find_urls() are covered in tests/reddit/test_reddit.py


def _client(handler) -> httpx.AsyncClient:
    """The production-configured client, answered by handler"""
    return mock_http_bundle(handler).http


def _image(content=b"data", content_type="image/jpeg"):
    return httpx.Response(200, headers={"Content-Type": content_type}, content=content)


def _responses(*results):
    """A handler that returns (or raises) each of results in turn, recording calls"""
    remaining = list(results)
    calls: list[httpx.Request] = []

    def handler(request):
        calls.append(request)
        result = remaining.pop(0)
        if isinstance(result, Exception):
            raise result
        if isinstance(result, httpx.Response):
            return result
        return httpx.Response(result)

    return handler, calls


class _FileTestCase(unittest.IsolatedAsyncioTestCase):
    """Gives each test a file manager in a fresh temp directory"""

    organize = False

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.manager = UniqueDirectoryFileManager(
            self._tmp.name, organize=self.organize
        )

    def files(self) -> dict[str, bytes]:
        """Every file saved, by path relative to the run's directory"""
        found = {}
        for root, _, names in os.walk(self.manager.directory):
            for name in names:
                path = os.path.join(root, name)
                with open(path, "rb") as f:
                    found[os.path.relpath(path, self.manager.directory)] = f.read()
        return found


class TestDownloadToFile(_FileTestCase):

    async def _download(self, client, **kwargs):
        return await _download_to_file(
            client,
            "https://x/u",
            self.manager,
            self.manager.directory,
            "T",
            backoff=0,
            **kwargs,
        )

    async def test_writes_file_named_by_content_type(self):
        handler, calls = _responses(_image(b"png", "image/png"))
        path = await self._download(_client(handler))
        self.assertEqual(path, os.path.join(self.manager.directory, "T.png"))
        self.assertEqual(self.files(), {"T.png": b"png"})
        self.assertEqual(len(calls), 1)

    async def test_hard_error_is_not_retried(self):
        handler, calls = _responses(404)  # 404 is a hard error, not retryable
        self.assertIsNone(await self._download(_client(handler), attempts=3))
        self.assertEqual(len(calls), 1)
        self.assertEqual(self.files(), {})

    async def test_retries_transport_error_then_succeeds(self):
        handler, calls = _responses(httpx.ConnectError("x"), _image())
        self.assertIsNotNone(await self._download(_client(handler), attempts=3))
        self.assertEqual(len(calls), 2)

    async def test_retries_timeout_then_succeeds(self):
        handler, _ = _responses(httpx.ReadTimeout("x"), _image())
        self.assertIsNotNone(await self._download(_client(handler), attempts=3))

    async def test_retries_retryable_status_then_succeeds(self):
        handler, calls = _responses(503, 429, _image())
        self.assertIsNotNone(await self._download(_client(handler), attempts=3))
        self.assertEqual(len(calls), 3)

    async def test_gives_up_after_retryable_statuses(self):
        handler, calls = _responses(503, 502)
        self.assertIsNone(await self._download(_client(handler), attempts=2))
        self.assertEqual(len(calls), 2)

    async def test_gives_up_after_transport_errors(self):
        handler, calls = _responses(httpx.ConnectError("x"), httpx.ConnectError("x"))
        self.assertIsNone(await self._download(_client(handler), attempts=2))
        self.assertEqual(len(calls), 2)

    async def test_failure_partway_through_body_is_retried(self):
        class Dropped(httpx.AsyncByteStream):
            async def __aiter__(self):
                yield b"part"
                raise httpx.ReadError("connection dropped")

        handler, calls = _responses(
            httpx.Response(
                200, headers={"Content-Type": "image/png"}, stream=Dropped()
            ),
            _image(b"whole", "image/png"),
        )
        await self._download(_client(handler), attempts=2)
        # only the complete file, under the name the partial one had claimed
        self.assertEqual(self.files(), {"T.png": b"whole"})
        self.assertEqual(len(calls), 2)

    async def test_streams_to_disk(self):
        # chunks should reach disk as the body is read, rather than the whole
        # body being collected in memory first. The file object buffers up to
        # io.DEFAULT_BUFFER_SIZE (128 KiB on 3.14), so disk can lag by that much
        size, count = 1 << 16, 16
        path = os.path.join(self.manager.directory, "T.png")
        on_disk = []

        class Body(httpx.AsyncByteStream):
            async def __aiter__(self):
                for _ in range(count):
                    on_disk.append(os.path.getsize(path) if os.path.exists(path) else 0)
                    yield b"x" * size

        handler, _ = _responses(
            httpx.Response(200, headers={"Content-Type": "image/png"}, stream=Body())
        )
        await self._download(_client(handler))
        self.assertEqual(os.path.getsize(path), size * count)
        lag = io.DEFAULT_BUFFER_SIZE + size
        for k, written in enumerate(on_disk):
            self.assertGreaterEqual(written, k * size - lag)
        self.assertGreater(on_disk[-1], 0)

    async def test_retry_waits_for_retry_after(self):
        delays = []

        async def record(delay):
            delays.append(delay)

        handler, _ = _responses(
            httpx.Response(429, headers={"Retry-After": "7"}), 503, _image()
        )
        # no limiter: this is about when the url is retried; the host cooldown
        # the same 429 triggers is tested with the transport
        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        with patch("asyncio.sleep", record):
            path = await _download_to_file(
                client,
                "https://x/u",
                self.manager,
                self.manager.directory,
                "T",
                attempts=3,
                backoff=0.5,
            )
        self.assertIsNotNone(path)
        # Retry-After when it's longer than the backoff, the backoff otherwise
        self.assertEqual(delays, [7.0, 1.0])

    async def test_same_host_request_runs_during_backoff(self):
        # with one slot for the host, a second request must run while the first
        # waits to retry, which only works if waiting holds no slot
        first_failed = asyncio.Event()
        order = []

        def handler(request):
            order.append(request.url.path)
            if request.url.path == "/flaky" and not first_failed.is_set():
                first_failed.set()
                raise httpx.ConnectError("x")
            return _image()

        with (
            patch("src.core.client_bundle.MAX_PER_HOST", 1),
            patch("src.core.client_bundle.MAX_CONNECTIONS", 1),
        ):
            client = _client(handler)

        async def fetch(path, stem, **kwargs):
            return await _download_to_file(
                client,
                f"https://x{path}",
                self.manager,
                self.manager.directory,
                stem,
                **kwargs,
            )

        async def other():
            await first_failed.wait()
            return await fetch("/other", "other")

        flaky, other_path = await asyncio.gather(
            fetch("/flaky", "flaky", attempts=2, backoff=0.2), other()
        )
        self.assertIsNotNone(flaky)
        self.assertIsNotNone(other_path)
        self.assertEqual(order, ["/flaky", "/other", "/flaky"])


class TestUnsave(unittest.IsolatedAsyncioTestCase):

    async def test_calls_unsave(self):
        wrapper = SubmissionWrapperFactory()
        with patch.object(
            wrapper._submission,
            "unsave",
            new_callable=AsyncMock,
        ) as mock_unsave:

            await wrapper.unsave()
            mock_unsave.assert_awaited_once()


class TestDownload(_FileTestCase):

    def _wrapper(self, urls, title="Post", subreddit="pics"):
        wrapper = SubmissionWrapperFactory(title=title, subreddit=subreddit)
        wrapper.urls = urls
        return wrapper

    async def test_no_urls(self):
        requests = []
        client = _client(lambda request: requests.append(request))
        self.assertEqual(await self._wrapper([]).download(client, self.manager), [])
        self.assertEqual(requests, [])
        self.assertEqual(self.files(), {})

    async def test_single_url_is_named_after_post(self):
        handler, _ = _responses(_image(b"one"))
        paths = await self._wrapper(["https://x/1"]).download(
            _client(handler), self.manager
        )
        self.assertEqual(paths, [os.path.join(self.manager.directory, "Post.jpg")])
        self.assertEqual(self.files(), {"Post.jpg": b"one"})

    async def test_album_keeps_order_and_extensions(self):
        content_types = {
            "/3": "image/jpeg",
            "/1": "image/png",
            "/2": "image/gif",
            "/4": "video/webm",
        }

        async def handler(request):
            # finish out of order, so only position-based naming keeps order
            await asyncio.sleep(0.01 * (5 - int(request.url.path[1:])))
            return _image(request.url.path.encode(), content_types[request.url.path])

        wrapper = self._wrapper([f"https://x{path}" for path in content_types])
        paths = await wrapper.download(_client(handler), self.manager)

        expected = [
            os.path.join("Post", name) for name in ("0.jpg", "1.png", "2.gif", "3.webm")
        ]
        self.assertEqual(
            [os.path.relpath(p, self.manager.directory) for p in paths], expected
        )
        self.assertEqual(
            self.files(), dict(zip(expected, [b"/3", b"/1", b"/2", b"/4"], strict=True))
        )

    async def test_album_keeps_positions_when_one_fails(self):
        def handler(request):
            if request.url.path == "/missing":
                return httpx.Response(404)
            return _image(request.url.path.encode())

        wrapper = self._wrapper(["https://x/a", "https://x/missing", "https://x/c"])
        await wrapper.download(_client(handler), self.manager)
        self.assertEqual(
            self.files(),
            {
                os.path.join("Post", "0.jpg"): b"/a",
                os.path.join("Post", "2.jpg"): b"/c",
            },
        )

    async def test_empty_album_is_removed(self):
        wrapper = self._wrapper(["https://x/a", "https://x/b"])
        paths = await wrapper.download(
            _client(lambda request: httpx.Response(404)), self.manager
        )
        self.assertEqual(paths, [])
        self.assertEqual(os.listdir(self.manager.directory), [])

    async def test_follows_redirects(self):
        # a redirected image used to come back as a 3xx and be dropped
        def handler(request):
            if request.url.path == "/old":
                return httpx.Response(301, headers={"Location": "https://x/new"})
            return _image(b"png", "image/png")

        await self._wrapper(["https://x/old"]).download(_client(handler), self.manager)
        self.assertEqual(self.files(), {"Post.png": b"png"})


class TestDownloadOrganized(_FileTestCase):
    organize = True

    async def test_files_go_in_subreddit_folder(self):
        handler, _ = _responses(_image(b"1"), _image(b"2"), _image(b"3"))
        single = SubmissionWrapperFactory(title="One", subreddit="pics")
        single.urls = ["https://x/1"]
        album = SubmissionWrapperFactory(title="Two", subreddit="art")
        album.urls = ["https://x/2", "https://x/3"]
        client = _client(handler)
        await single.download(client, self.manager)
        await album.download(client, self.manager)
        self.assertEqual(
            self.files(),
            {
                os.path.join("pics", "One.jpg"): b"1",
                os.path.join("art", "Two", "0.jpg"): b"2",
                os.path.join("art", "Two", "1.jpg"): b"3",
            },
        )


class TestStr(unittest.TestCase):

    def test_str_contains_info(self):

        wrapper = SubmissionWrapperFactory()

        self.assertIn(wrapper.title, str(wrapper))
        self.assertIn(wrapper.subreddit, str(wrapper))
        self.assertIn(wrapper.author, str(wrapper))
        self.assertIn(wrapper.url, str(wrapper))


class TestHasUrls(unittest.TestCase):

    def test_has_urls_empty(self):
        wrapped = SubmissionWrapperFactory()
        wrapped.urls = []
        self.assertFalse(wrapped.has_urls())

    def test_has_urls_nonempty(self):
        wrapped = SubmissionWrapperFactory()
        wrapped.urls = ["https://example.com/a.jpg"]
        self.assertTrue(wrapped.has_urls())
