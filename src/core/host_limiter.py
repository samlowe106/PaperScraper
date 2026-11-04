import asyncio
import time
from collections import defaultdict
from collections.abc import AsyncIterator, Callable
from email.utils import parsedate_to_datetime

import httpx

# statuses whose Retry-After pauses the whole host, not just one request
_COOLDOWN_STATUS = {429, 503}

# the longest a server can make us wait; beyond this we'd rather give up on a url
MAX_RETRY_AFTER = 60.0


def retry_after_seconds(response: httpx.Response) -> float | None:
    """
    How long the response's Retry-After header asks us to wait, capped at
    MAX_RETRY_AFTER, or None if there's no usable header. The header is either
    a number of seconds or an HTTP date.
    """
    value = response.headers.get("Retry-After", "").strip()
    if not value:
        return None
    try:
        seconds = float(value)
    except ValueError:
        try:
            when = parsedate_to_datetime(value)
        except TypeError, ValueError:
            return None
        seconds = when.timestamp() - time.time()
    return min(max(seconds, 0.0), MAX_RETRY_AFTER)


class _ReleasingStream(httpx.AsyncByteStream):
    """A response body that frees the request's slots once it's closed"""

    def __init__(self, stream: httpx.AsyncByteStream, release: Callable[[], None]):
        self._stream = stream
        self._release = release

    async def __aiter__(self) -> AsyncIterator[bytes]:
        async for chunk in self._stream:
            yield chunk

    async def aclose(self) -> None:
        try:
            await self._stream.aclose()
        finally:
            self._release()


class HostLimitedTransport(httpx.AsyncBaseTransport):
    """
    Wraps a transport so that at most ``per_host`` requests to any one host, and
    ``total`` overall, are in flight. A request holds its slot until its body is
    closed, so streamed responses count too.

    ``total`` should equal the inner transport's connection pool size: then a
    request only reaches the pool once a connection is free, and never spends
    its timeout queuing for one. Waiting here has no timeout.

    A 429 or 503 with Retry-After pauses every request to that host, not just
    the one that got it.
    """

    def __init__(self, inner: httpx.AsyncBaseTransport, *, per_host: int, total: int):
        self._inner = inner
        self._total = asyncio.Semaphore(total)
        self._hosts: defaultdict[str, asyncio.Semaphore] = defaultdict(
            lambda: asyncio.Semaphore(per_host)
        )
        self._blocked_until: dict[str, float] = {}

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        host = request.url.host

        # loop: another request may extend the cooldown while we sleep
        while (delay := self._blocked_until.get(host, 0) - time.monotonic()) > 0:
            await asyncio.sleep(delay)

        # always host first, then total, so two requests can't each hold what
        # the other is waiting for
        host_slot = self._hosts[host]
        await host_slot.acquire()
        try:
            await self._total.acquire()
        except BaseException:
            host_slot.release()
            raise

        released = False

        def release() -> None:
            nonlocal released
            if not released:
                released = True
                self._total.release()
                host_slot.release()

        try:
            response = await self._inner.handle_async_request(request)
        except BaseException:
            release()
            raise

        if response.status_code in _COOLDOWN_STATUS and (
            wait := retry_after_seconds(response)
        ):
            self._blocked_until[host] = max(
                self._blocked_until.get(host, 0), time.monotonic() + wait
            )

        assert isinstance(response.stream, httpx.AsyncByteStream)
        return httpx.Response(
            status_code=response.status_code,
            headers=response.headers,
            stream=_ReleasingStream(response.stream, release),
            extensions=response.extensions,
        )

    async def aclose(self) -> None:
        await self._inner.aclose()
