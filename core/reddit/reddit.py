import json
import os
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, Iterable, Set

import praw
import requests
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

    def __init__(self, submission: Submission, dry: bool = True):
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
        self.response: requests.Response = None
        self.urls: Set[str] = set()

        # whether this post can be unsaved or not
        self.can_unsave = not dry

    def find_urls(self) -> None:
        """
        Parses this wrapper's associated url to find all relevant image urls,
        and populates this wrapper's urls field
        """
        self.urls = parsers.find_urls(self.url)

    def download_all(
        self, directory: str, title: str = None, organize: bool = False
    ) -> Dict[str, str]:
        """
        Downloads all urls and bundles them with their results
        :param directory: directory in which to download each file
        :param title: title that the final file should have
        :param organize: whether or not to organize the download directory by subreddit
        :return: a zipped list of each url bundled with a True if the download succeeded
        or False if that download failed
        """
        if organize:
            directory = os.path.join(directory, self.subreddit)
        if title is None:
            title = self.title
        urls_filepaths: Dict[str, str] = dict()
        for i, url in enumerate(self.urls):
            if organize:
                directory = os.path.join(
                    directory,
                    self.base_file_title,
                    self.base_file_title if i == 0 else f"{self.base_file_title} ({i})",
                )
            else:
                destination = os.path.join(
                    directory,
                    self.base_file_title if i == 0 else f"{self.base_file_title} ({i})",
                )
            urls_filepaths[url] = (
                destination if self._download_image(url, destination) else None
            )
        return urls_filepaths

    def _download_image(self, url: str, directory: str) -> bool:
        """
        Downloads the linked image, converts it to the specified filetype,
        and saves to the specified directory. Avoids name conflicts.
        :param url: url directly linking to the image to download
        :param title: title that the final file should have
        :param temp_dir: directory that the final file should be saved to
        :return: True if the file was downloaded correctly, else False
        """
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return False
        os.makedirs(directory, exist_ok=True)
        with open(
            os.path.join(directory, self.title + core.get_extension(response)), "wb"
        ) as image_file:
            image_file.write(response.content)
        return True

    def log(self, file: str) -> None:
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

    def summary_string(self, index: int) -> str:
        """Generates a string that summarizes this post. Designed for CLI mode"""
        return self.format(
            f"({index}) %t\n   r/%s\n   %u\n   Saved %p / %f image(s) so far."
        )

    def unsave(self) -> None:
        """Unsaves this submission"""
        self._submission.unsave()

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


def from_source(
    source: ListingGenerator, limit: int = None, dry: bool = True
) -> Iterable[SubmissionWrapper]:
    """
    Wraps the submissions from the given source, and returns a generator that will generate at most
    limit items
    """

    def refill_batch():
        submissions = [s for i, s in enumerate(source) if i < 2 * limit]
        # TODO: why was asyncio.gather used here?
        wrappers = [SubmissionWrapper(s, dry) for s in submissions]
        return filter(lambda x: len(x.urls) > 0, wrappers)

    def submission_generator() -> Iterable[SubmissionWrapper]:
        yielded = 0
        batch = []
        while yielded < limit:
            batch = refill_batch()
            for item in batch:
                yielded += 1
                yield item

    return submission_generator()


def from_saved_posts(
    redditor: Redditor,
    score: int = None,
    age: timedelta = None,
    limit: int = None,
    dry: bool = True,
) -> Iterable[SubmissionWrapper]:
    """Generates a source of SubmissionWrappers from the given users' saved posts"""
    if limit < 1 or limit is None:
        raise ValueError("Limit must be a positive integer")
    return from_source(
        redditor.saved(limit=None, score=score, age=age), limit=limit, dry=dry
    )


def from_subreddit(
    subreddit_name: str,
    sortby: SortOption,
    score: int = None,
    age: timedelta = None,
    limit: int = 10,
) -> Iterable[SubmissionWrapper]:
    """Generates a source from a subreddit"""
    if limit < 1 or limit is None:
        raise ValueError("Limit must be a positive integer")
    return from_source(
        sortby(REDDIT.subreddit(subreddit_name.rstrip("r/")), score=score, age=age),
        limit=limit,
    )
