import asyncio
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Set

import requests
from praw.models import Submission

import core
from core import parsers


class SubmissionWrapper:
    """Wraps Submission objects to provide extra functionality"""

    def __init__(self, submission: Submission):
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

    async def find_urls(self) -> bool:
        """
        Parses this wrapper's associated url to find all relevant image urls,
        and populates this wrapper's urls field
        :returns: True if no problems were encountered while scraping this wrapper's url, else False
        """
        self.response = requests.get(
            self._submission.url,
            headers={"Content-type": "content_type_value"},
            timeout=10,
        )
        if self.response.status_code == 200:
            self.urls = asyncio.run(parsers.find_urls(self.response))
            return True
        return False

    async def download_all(self, directory: str, title: str = None) -> Dict[str, str]:
        """
        Downloads all urls and bundles them with their results
        :param directory: directory in which to download each file
        :return: a zipped list of each url bundled with a True if the download succeeded
        or False if that download failed
        """
        if title is None:
            title = self.title
        urls_filepaths: Dict[str, str] = dict()
        for i, url in enumerate(self.urls):
            destination = os.path.join(
                directory,
                self.base_file_title if i == 0 else f"{self.base_file_title} ({i})",
            )
            urls_filepaths[url] = (
                destination if await self._download_image(url, destination) else None
            )
        return urls_filepaths

    async def _download_image(self, url: str, directory: str) -> bool:
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

    def score_at_least(self, score_minimum: Optional[int]) -> bool:
        """
        True if this post has at least as much score as the given minimum, else False
        """
        if score_minimum is None:
            return True
        return score_minimum is None or self.score >= score_minimum

    def older_than(self, delta: Optional[timedelta]) -> bool:
        """
        True if this post is older than the given delta, else False
        """
        if delta is None:
            return True
        return datetime.now(timezone.utc) - self.time_created >= delta

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
