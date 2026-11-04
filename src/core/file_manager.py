import asyncio
import contextlib
import itertools
import json
import os
from collections.abc import AsyncIterable, Iterator
from datetime import datetime

import aiofiles
import aiofiles.os

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

    async def post_directory(self, subreddit: str | None = None) -> str:
        """
        The directory a post's files go in, created if needed: the subreddit's
        folder when organizing, otherwise this run's directory
        """
        if self.organize and subreddit:
            directory = os.path.join(self.directory, subreddit)
            # shared by every post from the subreddit, so it need not be unique
            await aiofiles.os.makedirs(directory, exist_ok=True)
            return directory
        return self.directory

    async def make_album(self, directory: str, title: str) -> str:
        """Creates a new album folder in directory named after title"""
        return await self._mkdir_unique(directory, title)

    @staticmethod
    async def discard_if_empty(directory: str) -> None:
        """Removes directory if nothing was saved into it"""
        with contextlib.suppress(OSError):
            await aiofiles.os.rmdir(directory)

    async def write_unique(
        self,
        directory: str,
        title: str,
        extension: str,
        chunks: AsyncIterable[bytes],
    ) -> str:
        """
        Writes chunks, as they arrive, to a new file in directory named after
        title, appending " (1)", " (2)", ... until the name is free. If writing
        fails partway, the partial file is removed (freeing its name) and the
        error re-raised.
        :return: the path that was written to
        """
        # exclusive creation ("xb") makes checking and claiming a name one step,
        # so concurrent saves of same-titled posts can't pick the same file
        for name in self.unique_names(title, extension):
            path = os.path.join(directory, name)
            try:
                file = await aiofiles.open(path, "xb")
            except FileExistsError:
                continue
            try:
                try:
                    async for chunk in chunks:
                        await file.write(chunk)
                finally:
                    await file.close()
            except BaseException:
                with contextlib.suppress(FileNotFoundError):
                    await aiofiles.os.remove(path)
                raise
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
