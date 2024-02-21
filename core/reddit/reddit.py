import asyncio
import json
import os
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, Iterable, List, Set, Tuple, Union

import httpx
import praw
from praw.models import ListingGenerator, Redditor, Submission
from praw.models.subreddits import Subreddit

import core
from core import parsers

REDDIT: praw.Reddit = None


def sign_in(username: str = None, password: str = None) -> praw.Reddit:
    """
    Signs in to reddit

    :raises OAuthException:
    """
    if username and password:
        return praw.Reddit(
            client_id=os.environ.get("CLIENT_ID"),
            client_secret=os.environ.get("CLIENT_SECRET"),
            user_agent="PaperScraper",
            username=username,
            password=password,
        )
    REDDIT = praw.Reddit(
        client_id=os.environ.get("CLIENT_ID"),
        client_secret=os.environ.get("CLIENT_SECRET"),
        user_agent="PaperScraper",
    )
    return REDDIT


class SubmissionWrapper:
    """Wraps Submission objects to provide extra functionality"""

    def __init__(
        self, submission: Submission, client: httpx.AsyncClient, dry: bool = True
    ):
        self._submission = submission

        # relevant to user
        self.title: str = submission.title
        self.subreddit = str(submission.subreddit)
        self.url: str = submission.url
        self.author = str(submission.author)
        self.nsfw: bool = submission.over_18
        self.score: int = submission.score
        self.time_created = datetime.fromtimestamp(submission.created_utc, timezone.utc)

        # relevant to parsing
        self.base_file_title = core.file_title(self._submission.title)
        self.response: httpx.Response = None
        self.urls: Set[str] = None

        # whether this post can be unsaved or not
        self.can_unsave = not dry

    async def find_urls(self, client: httpx.AsyncClient) -> None:
        self.urls = await parsers.find_urls(self.url, client)

    async def download_all(
        self,
        directory: str,
        client: httpx.AsyncClient,
        title: str = None,
        organize: bool = False,
    ) -> Dict[str, Union[str, None]]:
        """
        Downloads all urls and bundles them with their results
        :param directory: directory in which to download each file
        :client: the httpx.AsyncClient to use for downloading
        :param title: title that the final file should have
        :param organize: whether or not to organize the download directory by subreddit
        :return: a dictionary where the keys are this submission's urls and the values are the
        filepaths to which those images were downloaded or None if the download failed
        """
        urls_filepaths: Dict[str, Union[str, None]] = {url: None for url in self.urls}
        if len(urls_filepaths) == 0:
            return urls_filepaths
        if organize:
            directory = os.path.join(directory, self.subreddit)
        os.makedirs(directory, exist_ok=True)
        if title is None:
            title = self.title

        async def zip_result(url: str) -> Tuple[str, httpx.Response]:
            return (url, await client.get(self.url, timeout=10))

        urls_responses: List[
            Tuple[str, Union[httpx.Response, None]]
        ] = await asyncio.gather(zip_result(url) for url in self.urls)

        for i, pair in enumerate(urls_responses):
            url, response = pair
            if response is None or response.status_code != 200:
                continue
            filename = (
                title + core.get_extension(response)
                if len(self.response) == 1
                else f"{title} ({i+1}){core.get_extension(response)}"
            )
            destination = os.path.join(directory, filename)
            with open(destination, "wb") as image_file:
                image_file.write(response.content)
            urls_filepaths[url] = destination

        return urls_filepaths

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
        return self.format("%t\n   r/%s\n   %u\n   Saved %p / %f image(s) so far.")

    def summary_string(self) -> str:
        """Generates a string that summarizes this post"""
        return self.format("%t\n   r/%s\n   %u\n   Saved %p / %f image(s) so far.")

    def unsave(self, force=False) -> bool:
        """
        Unsaves this submission
        :param force: True to unsave this submission, even if can_unsave is False
        :return: True if the submission was unsaved, else False
        """
        if force or self.can_unsave:
            self._submission.unsave()
            return True
        return False

    def format(self, template: str, token="%") -> str:
        """
        Formats a string based on the given template.

        Each possible specifier is given below:

        t: current title
        T: current title in Title Case
        s: subreddit
        a: author
        u: submission's url
        p: number of parsed urls
        f: number of found urls
        (token): the token

        :param template: the template to base the output string on
        :param token: the token that prefixes each specifier
        :return: the formatted string
        """
        specifier_found = False
        string_list = []

        specifier_map = {
            "t": self.title,
            "T": core.title_case(self.title),
            "s": self.subreddit,
            "a": self.author,
            "u": self.url,
            token: token,
        }

        for i, char in enumerate(template):
            if specifier_found:
                if char not in specifier_map:
                    raise ValueError(
                        f"The given string contains a malformed specifier:\n{template}\n{i*' '}^"
                    )
                string_list.append(specifier_map[char])
                specifier_found = False
            elif char == token:
                specifier_found = True
            else:
                string_list.append(char)

        if specifier_found:
            # A format specifier began but was not finished, so this template is malformed
            raise ValueError("The given string contains a trailing token")

        return "".join(string_list)


class SortOption(Enum):
    """
    Represents the ways a subreddit's submissions can be sorted
    """

    def TOP_ALL(subreddit, **kwargs):
        return Subreddit.top(self=subreddit, time_filter="all", **kwargs)

    def TOP_DAY(subreddit, **kwargs):
        return Subreddit.top(self=subreddit, time_filter="day", **kwargs)

    def TOP_HOUR(subreddit, **kwargs):
        return Subreddit.top(self=subreddit, time_filter="hour", **kwargs)

    def TOP_WEEK(subreddit, **kwargs):
        return Subreddit.top(self=subreddit, time_filter="week", **kwargs)

    def TOP_MONTH(subreddit, **kwargs):
        return Subreddit.top(self=subreddit, time_filter="month", **kwargs)

    def TOP_YEAR(subreddit, **kwargs):
        return Subreddit.top(self=subreddit, time_filter="year", **kwargs)

    NEW = Subreddit.new
    HOT = Subreddit.hot
    CONTROVERSIAL = Subreddit.controversial
    GILDED = Subreddit.gilded

    def __call__(self, *args, **kwargs):
        self.value(*args, **kwargs)


async def _from_source(
    source: ListingGenerator, amount: int, client: httpx.AsyncClient, dry: bool = True
) -> List[SubmissionWrapper]:
    """
    Wraps the submissions from the given source, and returns a generator that will generate at most
    limit items
    """
    if amount < 1:
        raise ValueError("Desired must be a positive integer")
    batch: List[SubmissionWrapper] = []
    exhausted = False
    while not exhausted and len(batch) < amount:
        submissions: List[SubmissionWrapper] = []
        for i in range(amount - len(batch)):
            try:
                batch.append(next(source))
            except StopIteration:
                exhausted = True
                break
        wrappers = [SubmissionWrapper(s, client, dry=dry) for s in submissions]
        asyncio.gather(wrapper.find_urls(client) for wrapper in wrappers)
        batch += list(filter(lambda x: len(x.urls) > 0, wrappers))  # type: ignore
    return batch


async def from_saved(
    redditor: Redditor,
    amount: int,
    client: httpx.AsyncClient,
    score: int = None,
    age: timedelta = None,
    dry: bool = True,
) -> List[SubmissionWrapper]:
    """Generates a batch of at most (amount) SubmissionWrappers from the given users' saved posts"""
    if amount < 1:
        raise ValueError("Limit must be a positive integer")
    return await _from_source(
        redditor.saved(limit=None, score=score, age=age), amount, client, dry=dry
    )


async def from_subreddit(
    subreddit_name: str,
    sortby: SortOption,
    client: httpx.AsyncClient,
    score: int = None,
    age: timedelta = None,
    amount: int = 10,
) -> Iterable[SubmissionWrapper]:
    """Generates a batch of at most (amount) SubmissionWrappers from the given subreddit"""
    if amount < 1:
        raise ValueError("Limit must be a positive integer")
    return await _from_source(
        sortby(REDDIT.subreddit(subreddit_name.rstrip("r/")), score=score, age=age),
        amount,
        client,
    )
