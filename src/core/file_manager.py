import asyncio
import itertools
import json
import os
from collections.abc import Iterator
from datetime import datetime

import aiofiles
import aiofiles.os

# (content, extension) pairs; extensions keep their leading dot, e.g. ".jpg"
type DownloadsExtensions = list[tuple[bytes, str]]

# most filesystems cap a single path component at 255 bytes (not characters)
MAX_NAME_BYTES = 255

# characters that are invalid in file and directory names on at least one OS
_INVALID_CHARS = set(r'\/:*?"<>|') | {chr(c) for c in range(32)}


class UniqueDirectoryFileManager:
    def __init__(self, directory, organize=False):
        # this will essentially be the working directory,
        #  all files will be downloaded to this directory or its subdirectories
        # local (naive) time is intentional: the folder name should match the
        # user's clock. no colons, since they're invalid on Windows
        os.makedirs(directory, exist_ok=True)
        self.directory = self._mkdir_unique_sync(
            directory,
            datetime.today().strftime("PaperScraper %Y-%m-%d %H-%M"),  # noqa: DTZ002
        )
        self.organize = organize
        # serializes concurrent appends so log lines don't interleave
        self._log_lock = asyncio.Lock()

    async def log(self, record: dict, filename: str = "log.txt") -> str:
        """
        Appends a JSON record (one object per line) to a log file in this
        manager's directory.
        :param record: a JSON-serializable mapping describing the event
        :param filename: name of the log file within the managed directory
        :return: the path that was written to
        """
        path = os.path.join(self.directory, filename)
        line = json.dumps(record) + "\n"
        async with (
            self._log_lock,
            aiofiles.open(path, "a", encoding="utf-8") as logfile,
        ):
            await logfile.write(line)
        return path

    async def save_files(
        self,
        title: str,
        downloads: DownloadsExtensions,
        subreddit: str | None = None,
    ) -> list[str]:
        """
        Saves all files and bundles them with their results
        :param directory: directory in which to save each file
        :param title: title that the final file should have
        :param organize: whether or not to organize the save directory by subreddit
        :return: a list of filepaths to which the files were saved
        """

        if not downloads:
            return []

        directory = os.path.join(
            self.directory, subreddit if self.organize and subreddit else ""
        )
        # subreddit directory need not be unique
        await aiofiles.os.makedirs(directory, exist_ok=True)

        if len(downloads) == 1:
            # just one file, no need for a directory
            download, extension = downloads[0]
            return [await self._write_unique(directory, title, extension, download)]

        # album, need a directory to hold all the files
        directory = await self._mkdir_unique(directory, title)

        filepaths = [
            os.path.join(directory, f"{i}{extension}")
            for i, (_, extension) in enumerate(downloads)
        ]
        # write every file in the album concurrently
        await asyncio.gather(
            *(
                self._write(destination, download)
                for destination, (download, _) in zip(filepaths, downloads, strict=True)
            )
        )

        return filepaths

    @staticmethod
    async def _write(destination: str, content: bytes, mode: str = "wb") -> None:
        """Writes bytes to a path without blocking the event loop"""
        async with aiofiles.open(destination, mode) as f:
            await f.write(content)

    async def _write_unique(
        self, directory: str, title: str, extension: str, content: bytes
    ) -> str:
        """
        Writes content to a new file in directory named after title, appending
        " (1)", " (2)", ... until the name is free
        :return: the path that was written to
        """
        # exclusive creation ("xb") makes checking and claiming a name one step,
        # so concurrent saves of same-titled posts can't pick the same file
        for name in self.unique_names(title, extension):
            path = os.path.join(directory, name)
            try:
                await self._write(path, content, mode="xb")
            except FileExistsError:
                continue
            return path
        raise AssertionError("unreachable: unique_names is infinite")

    async def _mkdir_unique(self, parent: str, name: str) -> str:
        """Async version of _mkdir_unique_sync"""
        return await asyncio.to_thread(self._mkdir_unique_sync, parent, name)

    @classmethod
    def _mkdir_unique_sync(cls, parent: str, name: str) -> str:
        """
        Creates a new directory in parent named after name, appending " (1)",
        " (2)", ... until the name is free
        :return: the path of the created directory
        """
        for candidate in cls.unique_names(name):
            path = os.path.join(parent, candidate)
            try:
                os.mkdir(path)
            except FileExistsError:
                continue
            return path
        raise AssertionError("unreachable: unique_names is infinite")

    @classmethod
    def unique_names(cls, title: str, extension: str = "") -> Iterator[str]:
        """
        Yields valid names for title: "title.ext", then "title (1).ext", ...
        Each is shortened so that it fits in MAX_NAME_BYTES with its suffix.
        """
        title = cls.ensure_valid_filename(title)
        for offset in itertools.count():
            suffix = (f" ({offset})" if offset else "") + extension
            budget = MAX_NAME_BYTES - len(suffix.encode())
            yield _truncate_utf8(title, budget) + suffix

    @staticmethod
    def ensure_valid_filename(filename: str) -> str:
        """
        Replaces characters that are invalid in file or directory names with
        underscores
        :param filename: the filename to check
        :return: a valid filename with the same content as the input
        """
        cleaned = "".join("_" if c in _INVALID_CHARS else c for c in filename)
        # Windows drops trailing dots and spaces, and "", "." and ".." aren't
        # usable names anywhere
        cleaned = cleaned.rstrip(". ")
        return cleaned or "untitled"


def _truncate_utf8(text: str, max_bytes: int) -> str:
    """Cuts text to at most max_bytes of UTF-8 without splitting a character"""
    return text.encode()[:max_bytes].decode(errors="ignore")
