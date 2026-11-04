import asyncio
import unittest
from unittest.mock import AsyncMock, patch

import httpx

from src.reddit.submission_wrapper import _get_with_retry
from tests import SubmissionWrapperFactory, mock_http_bundle

# Note: log() and find_urls() are covered in tests/reddit/test_reddit.py


def _client(handler) -> httpx.AsyncClient:
    """The production-configured client, answered by handler"""
    return mock_http_bundle(handler).http


def _responses(*results):
    """A handler that returns (or raises) each of results in turn, recording calls"""
    remaining = list(results)
    calls: list[httpx.Request] = []

    def handler(request):
        calls.append(request)
        result = remaining.pop(0)
        if isinstance(result, Exception):
            raise result
        return httpx.Response(result)

    return handler, calls


class TestGetWithRetry(unittest.IsolatedAsyncioTestCase):

    async def _get(self, handler, **kwargs):
        return await _get_with_retry(
            _client(handler), "https://x/u", asyncio.Semaphore(1), backoff=0, **kwargs
        )

    async def test_returns_response_on_success(self):
        handler, calls = _responses(200)
        result = await self._get(handler)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(calls), 1)

    async def test_does_not_retry_hard_error(self):
        handler, calls = _responses(404)  # 404 is a hard error, not retryable
        result = await self._get(handler, attempts=3)
        self.assertEqual(result.status_code, 404)
        self.assertEqual(len(calls), 1)

    async def test_retries_transport_error_then_succeeds(self):
        handler, calls = _responses(httpx.ConnectError("x"), 200)
        result = await self._get(handler, attempts=3)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(calls), 2)

    async def test_retries_timeout_then_succeeds(self):
        handler, _ = _responses(httpx.ReadTimeout("x"), 200)
        result = await self._get(handler, attempts=3)
        self.assertEqual(result.status_code, 200)

    async def test_retries_retryable_status_then_succeeds(self):
        handler, calls = _responses(503, 429, 200)
        result = await self._get(handler, attempts=3)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(len(calls), 3)

    async def test_returns_last_response_when_statuses_exhaust_attempts(self):
        handler, _ = _responses(503, 502)
        result = await self._get(handler, attempts=2)
        self.assertEqual(result.status_code, 502)

    async def test_returns_none_when_transport_errors_exhaust_attempts(self):
        handler, calls = _responses(httpx.ConnectError("x"), httpx.ConnectError("x"))
        result = await self._get(handler, attempts=2)
        self.assertIsNone(result)
        self.assertEqual(len(calls), 2)

    async def test_releases_semaphore_during_backoff(self):
        # with one permit, a second request must run while the first is sleeping
        # between retries, which only works if backoff happens outside the permit
        semaphore = asyncio.Semaphore(1)
        first_failed = asyncio.Event()
        order = []

        def handler(request):
            order.append(request.url.path)
            if request.url.path == "/flaky" and not first_failed.is_set():
                first_failed.set()
                raise httpx.ConnectError("x")
            return httpx.Response(200)

        client = _client(handler)

        async def other():
            await first_failed.wait()
            return await _get_with_retry(client, "https://x/other", semaphore)

        flaky, other_result = await asyncio.gather(
            _get_with_retry(
                client, "https://x/flaky", semaphore, attempts=2, backoff=0.2
            ),
            other(),
        )
        assert flaky is not None and other_result is not None
        self.assertEqual(flaky.status_code, 200)
        self.assertEqual(other_result.status_code, 200)
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


class TestDownload(unittest.IsolatedAsyncioTestCase):

    async def test_download_empty(self):
        requests = []
        wrapper = SubmissionWrapperFactory()
        self.assertEqual(wrapper.urls, [])
        client = _client(lambda request: requests.append(request))
        self.assertEqual(await wrapper.download(client, asyncio.Semaphore(1)), [])
        self.assertEqual(requests, [])

    async def test_download_keeps_order_and_extensions(self):
        content_types = {
            "/3": "image/jpeg",
            "/1": "image/png",
            "/2": "image/gif",
            "/4": "video/webm",
        }

        async def handler(request):
            # finish out of order, so only gather's ordering keeps the result
            # in url order
            await asyncio.sleep(0.01 * (5 - int(request.url.path[1:])))
            return httpx.Response(
                200,
                headers={"Content-Type": content_types[request.url.path]},
                content=request.url.path.encode(),
            )

        wrapper = SubmissionWrapperFactory()
        wrapper.urls = [f"https://x{path}" for path in content_types]

        result = await wrapper.download(_client(handler), asyncio.Semaphore(4))

        self.assertEqual(
            result,
            [(b"/3", ".jpg"), (b"/1", ".png"), (b"/2", ".gif"), (b"/4", ".webm")],
        )

    async def test_download_follows_redirects(self):
        # a redirected image used to come back as a 3xx and be dropped
        def handler(request):
            if request.url.path == "/old":
                return httpx.Response(301, headers={"Location": "https://x/new"})
            return httpx.Response(
                200, headers={"Content-Type": "image/png"}, content=b"png"
            )

        wrapper = SubmissionWrapperFactory()
        wrapper.urls = ["https://x/old"]
        result = await wrapper.download(_client(handler), asyncio.Semaphore(1))
        self.assertEqual(result, [(b"png", ".png")])

    async def test_download_skips_failed_urls(self):
        # a url that exhausts retries or returns a hard error is dropped; others
        # still download
        def handler(request):
            if request.url.path == "/down":
                raise httpx.ConnectError("x")
            if request.url.path == "/missing":
                return httpx.Response(404)
            return httpx.Response(
                200, headers={"Content-Type": "image/jpeg"}, content=b"data"
            )

        wrapper = SubmissionWrapperFactory()
        wrapper.urls = ["https://x/good", "https://x/down", "https://x/missing"]
        with patch("asyncio.sleep", new_callable=AsyncMock):  # skip backoff
            result = await wrapper.download(_client(handler), asyncio.Semaphore(1))

        self.assertEqual(result, [(b"data", ".jpg")])

    async def test_in_flight_requests_never_exceed_semaphore(self):
        limit = 3
        semaphore = asyncio.Semaphore(limit)
        in_flight = 0
        peak = 0

        async def handler(request):
            nonlocal in_flight, peak
            in_flight += 1
            peak = max(peak, in_flight)
            await asyncio.sleep(0.01)
            in_flight -= 1
            return httpx.Response(
                200, headers={"Content-Type": "image/jpeg"}, content=b"data"
            )

        client = _client(handler)
        wrappers = []
        for i in range(4):
            wrapper = SubmissionWrapperFactory()
            wrapper.urls = [f"https://x/post{i}-img{j}" for j in range(5)]
            wrappers.append(wrapper)

        results = await asyncio.gather(
            *(wrapper.download(client, semaphore) for wrapper in wrappers)
        )

        self.assertEqual(peak, limit)
        self.assertEqual([len(r) for r in results], [5] * 4)


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
