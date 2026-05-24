import asyncio
import json

import asyncpraw
import httpx

from ..core import get_response_file_extension


class SubmissionWrapper:
    """Wraps Submission objects to provide extra functionality"""

    # created_utc: ???

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

    # def format(self, template: str) -> str:
    #    """
    #    Formats a template string using the submission wrapper's attributes.
    #    Supported tokens: %t title, %s subreddit, %u url, %p and %f number of found urls.
    #    """
    #    return (
    #        template.replace("%t", self.title)
    #        .replace("%s", self.subreddit)
    #        .replace("%u", self.url)
    #        .replace("%p", str(len(self.urls)))
    #        .replace("%f", str(len(self.urls)))
    #    )

    # def summary_string(self) -> str:
    #    """Generates a string that summarizes this post"""
    #    return self.format("%t\n   r/%s\n   %u\n   Saved %p / %f image(s) so far.")

    def has_urls(self) -> bool:
        """
        Returns True if this SubmissionWrapper has at least one url, else False
        """
        return len(self.urls) > 0
