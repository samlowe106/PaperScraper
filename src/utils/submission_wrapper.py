import json
import os
from typing import List, Tuple
import requests
from requests.models import Response
from praw.models import Submission
from utils import parsers, strings, urls

# Represents a tuple in the form (URL (str), whether the URL was correctly downloaded (bool))
URLTuple = Tuple[str, bool]


class SubmissionWrapper:
    """Wraps Submission objects to provide extra functionality"""

    response: Response = None
    urls: List[str] = []
    url_tuples: List[URLTuple] = []
    title: str = ""

    def __init__(self, submission: Submission):
        self.submission = submission
        self.title = strings.file_title(self.submission.title)

        r = requests.get(self.submission.url, headers={'Content-type': 'content_type_value'})

        if r.status_code == 200:
            self.response = r
            self.urls = parsers.find_urls(self.response)


    def download_all(self, directory: str) -> List[URLTuple]:
        """
        Downloads all urls and bundles them with their results
        :param directory: directory in which to download each file
        :return: a zipped list of each url bundled with a True if the download succeded
        or False if that download failed
        """
        results = [urls.download(url, self.title, directory) if i == 0
                   else urls.download(url,f'{self.title} ({i})', directory)
                   for i, url in enumerate(self.urls)]

        self.url_tuples = list(zip(urls, results))

        return self.url_tuples


    def download_image(self, url: str, directory: str) -> bool:
        """
        Downloads the linked image, converts it to the specified filetype,
        and saves to the specified directory. Avoids name conflicts.
        :param url: url directly linking to the image to download
        :param title: title that the final file should have
        :param temp_dir: directory that the final file should be saved to
        :return: True if the file was downloaded correctly, else False
        """
        r = requests.get(url)

        if r.status_code != 200:
            return False

        os.makedirs(directory, exist_ok=True)
        with open(os.path.join(directory, self.title + urls.get_extension(r)), "wb") as f:
            f.write(r.content)
        return True


    def count_parsed(self) -> int:
        """
        Counts the number of urls that were parsed
        :return: number of tuples that were correctly parsed
        """
        return [result for _, result in self.url_tuples].count(True)


    def fully_parsed(self) -> bool:
        """
        :return: True if urls were found and each one was parsed, else False
        """
        return self.url_tuples and self.count_parsed() == len(self.url_tuples)


    def log(self, file: str) -> None:
        """
        Writes the given post's title and url to the specified file
        :param file: log file path
        """
        with open(file, "a", encoding="utf-8") as logfile:
            json.dump({
                           "title"           : self.submission.title,
                           "id"              : self.submission.id,
                           "url"             : self.submission.url,
                           "recognized_urls" : self.url_tuples
                       }, logfile)


    def print_self(self, index: int) -> None:
        """
        Prints out information about the specified post
        :param index: the index number of the post
        :return: None
        """
        print(f"\n{index}. {self.submission.title}" \
              f"   r/{self.submission.subreddit}" \
              f"   {self.submission.url}" \
              f"   Saved {self.count_parsed()} / {len(self.url_tuples)} image(s).")


    def unsave(self):
        """ Unsaves the submission associated with this post """
        self.submission.unsave()
