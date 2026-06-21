import asyncio

import asyncpraw
import httpx

from ..core import AsyncClientBundle, get_response_file_extension
from ..parsing import find_urls as parse_find_urls

# transient statuses worth retrying (rate limit + gateway/server errors)
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


async def _get_with_retry(
    client: httpx.AsyncClient,
    url: str,
    *,
    attempts: int = 3,
    backoff: float = 0.5,
    timeout: float = 10,
) -> httpx.Response | None:
    """
    GETs ``url``, retrying transient transport errors and 429/5xx responses with
    exponential backoff. Returns the response once it's non-retryable (success or
    a hard error like 404), or ``None`` if every attempt failed at the transport
    level — so one persistently-broken url drops a single file rather than failing
    the whole submission.
    """
    response: httpx.Response | None = None
    for attempt in range(attempts):
        try:
            response = await client.get(url, timeout=timeout)
            if response.status_code not in _RETRYABLE_STATUS:
                return response
        except (httpx.TransportError, httpx.TimeoutException):
            response = None
        if attempt < attempts - 1:
            await asyncio.sleep(backoff * (2**attempt))
    return response


class SubmissionWrapper:
    """Wraps Submission objects to provide extra functionality"""

    def __init__(
        self,
        submission: asyncpraw.models.Submission,
        client: httpx.AsyncClient,
        dry: bool = True,
    ):
        self._submission = submission

        self.title = submission.title
        self.subreddit = str(submission.subreddit)
        self.url = submission.url
        self.author = str(submission.author)
        self.nsfw = submission.over_18
        self.score = submission.score
        self.created_utc = submission.created_utc
        self.urls: set[str] = set()

    async def unsave(self):
        """
        Unsaves this object
        """
        return await self._submission.unsave()

    async def download(
        self,
        client: httpx.AsyncClient,
    ) -> list[tuple[bytes, str]]:
        """
        Downloads all urls and bundles them with their file extension
        :client: the httpx client to use for downloading
        :return: a list of tuples, where the first element is
        the content of the downloaded file and the second element is the file extension
        """
        if not self.urls:
            return list()

        responses = await asyncio.gather(
            *(_get_with_retry(client, url) for url in self.urls)
        )

        return [
            (
                response.content,
                get_response_file_extension(response),
            )
            for response in responses
            if response is not None and response.status_code == 200
        ]

    async def find_urls(self, clients: AsyncClientBundle) -> set[str]:
        """
        Runs every parser against this submission's url and stores the resulting
        direct media links in ``self.urls``.
        :param clients: the full client bundle (parsers need http AND reddit)
        :return: the set of discovered urls (also stored on self.urls)
        """
        self.urls = await parse_find_urls(self.url, clients)
        return self.urls

    def log_record(self, exception: str = "") -> dict:
        """
        Builds a JSON-serializable record describing this post, suitable for
        handing to a logger (e.g. ``UniqueDirectoryFileManager.log``).
        """
        return {
            "title": self._submission.title,
            "id": self._submission.id,
            "url": self._submission.url,
            "recognized_urls": sorted(self.urls),  # set -> list for JSON
            "exception": exception,
        }

    def __str__(self) -> str:
        """
        Prints out information about the specified post
        :param index: the index number of the post
        :return: None
        """
        return f"{self.title} ({self.subreddit}) by {self.author} ({self.url})"

    def has_urls(self) -> bool:
        """
        Returns True if this SubmissionWrapper has at least one url, else False
        """
        return len(self.urls) > 0
