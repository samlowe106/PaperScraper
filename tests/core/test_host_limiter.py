import asyncio
import time
import unittest
from collections import Counter
from datetime import UTC, datetime, timedelta
from email.utils import format_datetime

import httpcore
import httpx

from src.core import HostLimitedTransport, make_http_client, retry_after_seconds
from src.core.client_bundle import MAX_CONNECTIONS, MAX_PER_HOST
from src.core.host_limiter import MAX_RETRY_AFTER


class _Tracker:
    """A mock-transport handler that records how many requests are in flight"""

    def __init__(self, delay=0.01):
        self.delay = delay
        self.in_flight: Counter[str] = Counter()
        self.peak_per_host: Counter[str] = Counter()
        self.peak_total = 0

    async def __call__(self, request):
        host = request.url.host
        self.in_flight[host] += 1
        self.peak_per_host[host] = max(self.peak_per_host[host], self.in_flight[host])
        self.peak_total = max(self.peak_total, self.in_flight.total())
        await asyncio.sleep(self.delay)
        self.in_flight[host] -= 1
        return httpx.Response(200, content=b"x")


def _client(handler, *, per_host, total):
    transport = HostLimitedTransport(
        httpx.MockTransport(handler), per_host=per_host, total=total
    )
    return httpx.AsyncClient(transport=transport, follow_redirects=True)


class TestLimits(unittest.IsolatedAsyncioTestCase):

    async def test_per_host_limit_with_hosts_in_parallel(self):
        tracker = _Tracker()
        client = _client(tracker, per_host=3, total=100)
        await asyncio.gather(
            *(client.get(f"https://{host}/{i}") for host in "ab" for i in range(10))
        )
        self.assertEqual(tracker.peak_per_host, Counter({"a": 3, "b": 3}))
        # the hosts didn't wait on each other
        self.assertEqual(tracker.peak_total, 6)

    async def test_total_limit(self):
        tracker = _Tracker()
        client = _client(tracker, per_host=3, total=4)
        await asyncio.gather(
            *(client.get(f"https://h{h}/{i}") for h in range(5) for i in range(3))
        )
        self.assertEqual(tracker.peak_total, 4)


class TestSlotLifetime(unittest.IsolatedAsyncioTestCase):

    async def test_slot_held_until_streamed_body_closes(self):
        client = _client(lambda request: httpx.Response(200), per_host=1, total=1)
        second = None
        async with client.stream("GET", "https://a/1"):
            # the first body is still open, so the host's only slot is taken
            second = asyncio.create_task(client.get("https://a/2"))
            await asyncio.sleep(0.05)
            self.assertFalse(second.done())
        self.assertEqual((await asyncio.wait_for(second, 1)).status_code, 200)

    async def test_slot_released_when_request_fails(self):
        def handler(request):
            if request.url.path == "/down":
                raise httpx.ConnectError("x")
            return httpx.Response(200)

        client = _client(handler, per_host=1, total=1)
        with self.assertRaises(httpx.ConnectError):
            await client.get("https://a/down")
        response = await asyncio.wait_for(client.get("https://a/up"), 1)
        self.assertEqual(response.status_code, 200)

    async def test_same_host_redirect_with_one_slot(self):
        # each hop needs the host's only slot, so the first must be freed first
        def handler(request):
            if request.url.path == "/old":
                return httpx.Response(301, headers={"Location": "/new"})
            return httpx.Response(200, content=b"new")

        client = _client(handler, per_host=1, total=1)
        response = await asyncio.wait_for(client.get("https://a/old"), 1)
        self.assertEqual(response.content, b"new")


class TestCooldown(unittest.IsolatedAsyncioTestCase):

    async def test_retry_after_pauses_only_that_host(self):
        started: dict[str, float] = {}

        def handler(request):
            started[str(request.url)] = time.monotonic()
            if request.url.path == "/limited":
                return httpx.Response(429, headers={"Retry-After": "0.3"})
            return httpx.Response(200)

        client = _client(handler, per_host=8, total=8)
        limited_at = time.monotonic()
        await client.get("https://a/limited")
        await asyncio.gather(client.get("https://a/next"), client.get("https://b/next"))

        self.assertGreaterEqual(started["https://a/next"] - limited_at, 0.3)
        self.assertLess(started["https://b/next"] - limited_at, 0.1)

    async def test_no_cooldown_without_header(self):
        def handler(request):
            return httpx.Response(429 if request.url.path == "/1" else 200)

        client = _client(handler, per_host=8, total=8)
        await client.get("https://a/1")
        before = time.monotonic()
        await client.get("https://a/2")
        self.assertLess(time.monotonic() - before, 0.1)


class TestMakeHttpClient(unittest.IsolatedAsyncioTestCase):

    async def test_limiter_wraps_pool_of_matching_size(self):
        # the limiter's total must equal the pool size, or requests queue in the
        # pool where waiting counts against their timeout
        client = make_http_client()
        transport = client._transport
        assert isinstance(transport, HostLimitedTransport)
        assert isinstance(transport._inner, httpx.AsyncHTTPTransport)
        pool = transport._inner._pool
        assert isinstance(pool, httpcore.AsyncConnectionPool)
        self.assertEqual(pool._max_connections, MAX_CONNECTIONS)
        self.assertEqual(transport._total._value, MAX_CONNECTIONS)
        self.assertEqual(transport._hosts["x"]._value, MAX_PER_HOST)
        await client.aclose()

    async def test_mock_transport_still_limited(self):
        tracker = _Tracker()
        client = make_http_client(transport=httpx.MockTransport(tracker))
        await asyncio.gather(*(client.get(f"https://a/{i}") for i in range(20)))
        self.assertEqual(tracker.peak_per_host["a"], MAX_PER_HOST)


class TestRetryAfterSeconds(unittest.TestCase):

    @staticmethod
    def _response(value=None):
        headers = {} if value is None else {"Retry-After": value}
        return httpx.Response(429, headers=headers)

    def test_seconds(self):
        self.assertEqual(retry_after_seconds(self._response("5")), 5.0)

    def test_http_date(self):
        when = datetime.now(UTC) + timedelta(seconds=30)
        seconds = retry_after_seconds(
            self._response(format_datetime(when, usegmt=True))
        )
        assert seconds is not None
        self.assertAlmostEqual(seconds, 30, delta=2)

    def test_past_date_is_zero(self):
        when = datetime.now(UTC) - timedelta(hours=1)
        self.assertEqual(
            retry_after_seconds(self._response(format_datetime(when, usegmt=True))), 0
        )

    def test_capped(self):
        self.assertEqual(retry_after_seconds(self._response("3600")), MAX_RETRY_AFTER)

    def test_missing_or_garbage(self):
        for value in [None, "", "soon"]:
            with self.subTest(value):
                self.assertIsNone(retry_after_seconds(self._response(value)))
