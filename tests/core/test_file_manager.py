import unittest
from datetime import datetime
from unittest.mock import patch

from src.core import UniqueDirectoryFileManager


class TestUniqueDirectoryFileManagerConstructor(unittest.TestCase):
    now = datetime(2000, 1, 2, 12, 0, 0)

    @patch("src.core.file_manager.datetime", return_value=now)
    @patch("os.makedirs")
    def test_correct_directory_name(self, mock_os_makedirs, mock_datetime):
        # this should run on linux
        mock_datetime.today.return_value = self.now
        manager = UniqueDirectoryFileManager("mock_directory")
        self.assertEqual(
            manager.directory, "mock_directory/PaperScraper 2000-01-02 12:00"
        )
        mock_os_makedirs.assert_called_once_with(
            "mock_directory/PaperScraper 2000-01-02 12:00", exist_ok=False
        )


class TestSaveFiles(unittest.TestCase):
    pass


class TestGetUniqueFilepath(unittest.TestCase):
    pass


class TestEnsureValidFilename(unittest.TestCase):
    pass


class TestGetUniqueDirname(unittest.TestCase):
    pass


class TestEnsureValidDirname(unittest.TestCase):
    pass


r"""
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

    def save_files(
        self,
        title: str,
        downloads: DownloadsExtensions,
        subreddit: str = None,
    ) -> list[str]:
        if not downloads:
            return []

        directory = os.path.join(self.directory, subreddit if self.organize else "")
        os.makedirs(directory, exist_ok=True)  # subreddit directory need not be unique

        if len(downloads) == 1:
            # just one file, no need for a directory
            download, extension = downloads[0]
            filepath = self.get_unique_filepath(directory, title, extension)
            with open(filepath, "wb") as f:
                f.write(download)
            return [filepath]

        # album, need a directory to hold all the files
        directory = os.path.join(directory, self.get_unique_dirname(title))
        os.makedirs(directory, exist_ok=False)  # album directory should be unique

        filepaths = []
        for i, (download, extension) in enumerate(downloads):
            destination = os.path.join(directory, f"{i}.{extension}")
            with open(destination, "wb") as f:
                f.write(download)
            filepaths.append(destination)

        return filepaths

    def get_unique_filepath(
        self, directory: str, title: str, file_extension: str
    ) -> str:
        # this naive implementation may have bad big O runtime if there are a lot of duplicate
        #  filenames, and could be optimized by keeping a persistent counter for each title,
        #  but this should almost never happen in practice so this is good enough
        # ensure validity
        title = self.ensure_valid_filename(title)
        filename = f"{title}.{file_extension}"
        # ensure uniqueness
        offset = 0
        while filename in os.listdir(directory):
            offset += 1
            filename = f"{title} ({offset}).{file_extension}"
        return os.path.join(directory, filename)

    def ensure_valid_filename(self, filename: str) -> str:
        return "".join(c if c not in r'\/:*?"<>|' else "_" for c in filename)

    def get_unique_dirname(self, dirname):
        # ensure validity
        dirname = self.ensure_valid_dirname(dirname)
        # ensure uniqueness
        directory = os.path.join(self.directory, dirname)
        offset = 0
        while os.path.exists(directory):
            directory = os.path.join(self.directory, f"{dirname} ({offset})")
            offset += 1
        return directory

    def ensure_valid_dirname(self, dirname: str) -> str:
        return "".join(c if c not in r'\/:*?"<>|' else "_" for c in dirname)
"""
