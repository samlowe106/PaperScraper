import asyncio
import json
import os
from datetime import datetime

import aiofiles
import aiofiles.os

type DownloadsExtensions = list[tuple[bytes, str]]

# leave headroom under the typical 255-char filename limit for the extension
MAX_FILENAME_LENGTH = 250


class UniqueDirectoryFileManager:
    def __init__(self, directory, organize=False):
        # this will essentially be the woking directory,
        #  all files will be downloaded to this directory or its subdirectories
        self.directory = os.path.join(
            directory, datetime.today().strftime("PaperScraper %Y-%m-%d %H:%M")
        )
        # we can assume that this directory does not already exist
        #  if it does, that's basically intentional from the user
        os.makedirs(self.directory, exist_ok=False)
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
        async with self._log_lock:
            async with aiofiles.open(path, "a", encoding="utf-8") as logfile:
                await logfile.write(line)
        return path

    async def save_files(
        self,
        title: str,
        downloads: DownloadsExtensions,
        subreddit: str = None,
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

        directory = os.path.join(self.directory, subreddit if self.organize else "")
        # subreddit directory need not be unique
        await aiofiles.os.makedirs(directory, exist_ok=True)

        if len(downloads) == 1:
            # just one file, no need for a directory
            download, extension = downloads[0]
            filepath = await self.get_unique_filepath(directory, title, extension)
            await self._write(filepath, download)
            return [filepath]

        # album, need a directory to hold all the files
        directory = os.path.join(directory, await self.get_unique_dirname(title))
        # album directory should be unique
        await aiofiles.os.makedirs(directory, exist_ok=False)

        filepaths = [
            os.path.join(directory, f"{i}.{extension}")
            for i, (_, extension) in enumerate(downloads)
        ]
        # write every file in the album concurrently
        await asyncio.gather(
            *(
                self._write(destination, download)
                for destination, (download, _) in zip(filepaths, downloads)
            )
        )

        return filepaths

    @staticmethod
    async def _write(destination: str, content: bytes) -> None:
        """Writes bytes to a path without blocking the event loop"""
        async with aiofiles.open(destination, "wb") as f:
            await f.write(content)

    async def get_unique_filepath(
        self, directory: str, title: str, file_extension: str
    ) -> str:
        """
        Gets a unique filename in the specified directory with the specified title as a prefix
        :param title: the prefix for the filename
        :param directory: the directory in which to check for filename conflicts
        :param file_extension: the file extension for the filename
        :return: a unique filename in the specified directory with the specified title as a prefix
        """
        # this naive implementation may have bad big O runtime if there are a lot of duplicate
        #  filenames, and could be optimized by keeping a persistent counter for each title,
        #  but this should almost never happen in practice so this is good enough
        # ensure validity
        title = self.ensure_valid_filename(title)
        filename = f"{title}.{file_extension}"
        # ensure uniqueness
        offset = 0
        existing = await aiofiles.os.listdir(directory)
        while filename in existing:
            offset += 1
            filename = f"{title} ({offset}).{file_extension}"
        return os.path.join(directory, filename)

    def ensure_valid_filename(self, filename: str) -> str:
        """
        Replaces characters that are invalid in filenames with underscores and
        caps the length so long titles can't exceed the OS filename limit
        :param filename: the filename to check
        :return: a valid filename with the same content as the input
        """
        cleaned = "".join(c if c not in r'\/:*?"<>|' else "_" for c in filename)
        return cleaned[:MAX_FILENAME_LENGTH]

    async def get_unique_dirname(self, dirname):
        """
        Gets a unique directory name in the current directory with the specified name as a prefix
        :param dirname: the prefix for the directory name
        :return: a unique directory name in the current directory with the specified name as a prefix
        """
        # ensure validity
        dirname = self.ensure_valid_dirname(dirname)
        # ensure uniqueness
        directory = os.path.join(self.directory, dirname)
        offset = 0
        while await aiofiles.os.path.exists(directory):
            directory = os.path.join(self.directory, f"{dirname} ({offset})")
            offset += 1
        return directory

    def ensure_valid_dirname(self, dirname: str) -> str:
        """
        Replaces characters that are invalid in directory names with underscores
        :param dirname: the directory name to check
        :return: a valid directory name with the same content as the input
        """
        return "".join(c if c not in r'\/:*?"<>|' else "_" for c in dirname)
