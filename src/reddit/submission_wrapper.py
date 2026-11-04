import asyncio

import asyncpraw
import asyncpraw.models
import httpx

from ..core import (
    AsyncClientBundle,
    UniqueDirectoryFileManager,
    get_response_file_extension,
    retry_after_seconds,
)
from ..parsing import find_urls as parse_find_urls
from ..parsing import media_urls

# transient statuses worth retrying (rate limit + gateway/server errors)
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


async def _download_to_file(
    client: httpx.AsyncClient,
    url: str,
    file_manager: UniqueDirectoryFileManager,
    directory: str,
    stem: str,
    *,
    attempts: int = 3,
    backoff: float = 0.5,
    timeout: float = 10,
) -> str | None:
    """
    Streams ``url`` into a new file in ``directory`` named ``stem`` plus the
    extension its Content-Type implies, so the file never sits in memory.
    Retries transient transport errors (including ones partway through the
    body) and 429/5xx responses with exponential backoff, or as long as the
    server's Retry-After asks if that's longer.
    :return: the path written, or None if the url couldn't be downloaded (a
    hard error like 404, or every attempt failed), so one broken url drops a
    single file rather than failing the whole submission
    """
    for attempt in range(attempts):
        retry_after = None
        try:
            async with client.stream("GET", url, timeout=timeout) as response:
                if response.status_code == 200:
                    return await file_manager.write_unique(
                        directory,
                        stem,
                        get_response_file_extension(response),
                        response.aiter_bytes(),
                    )
                if response.status_code not in _RETRYABLE_STATUS:
                    return None
                retry_after = retry_after_seconds(response)
        # write_unique has already removed any partial file
        except httpx.TransportError, httpx.TimeoutException:
            pass
        if attempt < attempts - 1:
            # concurrency is limited by the client's transport, which holds no
            # slot while this waits
            await asyncio.sleep(max(backoff * (2**attempt), retry_after or 0))
    return None


class SubmissionWrapper:
    """Wraps Submission objects to provide extra functionality"""

    def __init__(self, submission: asyncpraw.models.Submission):
        self._submission = submission

        self.title = submission.title
        self.subreddit = str(submission.subreddit)
        self.url = submission.url
        self.author = str(submission.author)
        self.nsfw = submission.over_18
        self.score = submission.score
        self.created_utc = submission.created_utc
        self.urls: list[str] = []

    async def unsave(self):
        """
        Unsaves this object
        """
        return await self._submission.unsave()

    async def download(
        self, client: httpx.AsyncClient, file_manager: UniqueDirectoryFileManager
    ) -> list[str]:
        """
        Streams every url to disk: one url to a file named after the post,
        several to an album folder of files numbered by position. A url that
        fails is skipped and the others keep their positions.
        :return: the paths written, in url order
        """
        if not self.urls:
            return []

        directory = await file_manager.post_directory(self.subreddit)
        album = len(self.urls) > 1
        if album:
            directory = await file_manager.make_album(directory, self.title)
            stems = [str(i) for i in range(len(self.urls))]
        else:
            stems = [self.title]

        # a TaskGroup rather than gather: if one file fails outright (disk
        # full), the rest are cancelled, cleaning up their partial files,
        # instead of carrying on after the post has been given up on
        async with asyncio.TaskGroup() as task_group:
            tasks = [
                task_group.create_task(
                    _download_to_file(client, url, file_manager, directory, stem)
                )
                for url, stem in zip(self.urls, stems, strict=True)
            ]
        saved = [path for task in tasks if (path := task.result()) is not None]

        if album and not saved:
            await file_manager.discard_if_empty(directory)
        return saved

    async def find_urls(self, clients: AsyncClientBundle) -> list[str]:
        """
        Runs every parser against this submission's url and stores the resulting
        direct media links in ``self.urls``.
        :param clients: the full client bundle (parsers need http AND reddit)
        :return: the discovered urls, in order (also stored on self.urls)
        """
        # reddit-hosted images and galleries come with the listing; only other
        # links need the parsers (and their requests)
        self.urls = media_urls(self._submission) or await parse_find_urls(
            self.url, clients
        )
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
            "recognized_urls": list(self.urls),
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
