import datetime
import os
import re

type DownloadsExtensions = list[tuple[bytes, str]]

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
        while filename in os.listdir(directory):
            offset += 1
            filename = f"{title} ({offset}).{file_extension}"
        return os.path.join(directory, filename)

    def ensure_valid_filename(self, filename: str) -> str:
        """
        Replaces characters that are invalid in filenames with underscores
        :param filename: the filename to check
        :return: a valid filename with the same content as the input
        """
        return "".join(c if c not in r'\/:*?"<>|' else "_" for c in filename)

    def get_unique_dirname(self, dirname):
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
        while os.path.exists(directory):
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
