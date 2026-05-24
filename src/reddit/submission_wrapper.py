import asyncio
import json
import re
from asyncio import Future
from dataclasses import dataclass

import asyncpraw
import httpx

from ..core import get_response_file_extension

INVALID_WINDOWS_CHARS = r'<>:"/\|?*'


def retitle(s: str) -> str:
    """
    Creates a valid filename based on the given title string without duplicate whitespace or
    leading/trailing punctuation
    :param s: the string that the created filename should be based on
    :return: a valid, aesthetically pleasing filename
    """
    # remove characters that windows doesn't allow in filenames
    s = s.replace('"', "'")
    for char in INVALID_WINDOWS_CHARS:
        s = s.replace(char, "")

    # remove any duplicate whitespace
    s = " ".join(s.split())

    # trim punctuation ("." and ",") from the start and end of the string
    r = re.compile(r"^([\.,]*)([^\.,]*)([\.,]*)\Z")
    s = r.match(s).group(2)

    return s[:250]


async def urls_responses(
    urls: str, client: httpx.AsyncClient
) -> Future[list[tuple[str, httpx.Response]]]:
    """
    Gets the responses for a list of urls
    :param urls: a list of urls to get responses for
    :param client: the httpx.AsyncClient to use for getting responses
    :return: a list of tuples, where the first element is the url and the second element is the response for that url
    """

    async def fetch(url: str) -> tuple[str, httpx.Response]:
        return url, await client.get(url, timeout=10)

    return asyncio.gather(*(fetch(url) for url in urls))


@dataclass
class SubmissionWrapper:
    """Wraps Submission objects to provide extra functionality"""

    _submission: asyncpraw.models.Submission
    title: str
    subreddit: str
    url: str
    author: str
    nsfw: bool
    score: int
    # created_utc: ???
    urls: set[str]
    response: httpx.Response

    def __init__(
        self,
        submission: asyncpraw.models.Submission,
        client: httpx.AsyncClient,
        dry: bool = True,
    ):
        self._submission = submission

        # relevant to user
        self.title = submission.title
        self.subreddit = str(submission.subreddit)
        self.url = submission.url
        self.author = str(submission.author)
        self.nsfw = submission.over_18
        self.score = submission.score
        self.created_utc = submission.created_utc
        self.urls = set()

        # relevant to parsing
        self.base_file_title = retitle(self._submission.title)
        self.response = None

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
        # TODO: add this to task_group?

        if not self.urls:
            return list()

        responses = await asyncio.gather(
            *(client.get(url, timeout=10) for url in self.urls)
        )

        return [
            (
                response.content,
                get_response_file_extension(response),
            )
            for response in responses
            if response.status_code == 200
        ]

    async def find_urls(client, *args, **kwargs):
        pass

    def log(self, file: str, exception: str = "") -> None:
        """
        Writes the given post's title and url to the specified file
        :param file: log file path
        """
        with open(file, "a", encoding="utf-8") as logfile:
            json.dump(
                {
                    "title": self._submission.title,
                    "id": self._submission.id,
                    "url": self._submission.url,
                    "recognized_urls": self.urls,
                    "exception": exception,
                },
                logfile,
            )

    def __str__(self) -> str:
        """
        Prints out information about the specified post
        :param index: the index number of the post
        :return: None
        """
        return f"{self.title} ({self.subreddit}) by {self.author} ({self.url})"
        # return self.format("%t\n   r/%s\n   %u\n   Saved %p / %f image(s) so far.")

    def format(self, template: str) -> str:
        """
        Formats a template string using the submission wrapper's attributes.
        Supported tokens: %t title, %s subreddit, %u url, %p and %f number of found urls.
        """
        return (
            template.replace("%t", self.title)
            .replace("%s", self.subreddit)
            .replace("%u", self.url)
            .replace("%p", str(len(self.urls)))
            .replace("%f", str(len(self.urls)))
        )

    def summary_string(self) -> str:
        """Generates a string that summarizes this post"""
        return self.format("%t\n   r/%s\n   %u\n   Saved %p / %f image(s) so far.")

    def has_urls(self) -> bool:
        """
        Returns True if this SubmissionWrapper has at least one url, else False
        """
        return len(self.urls) > 0
