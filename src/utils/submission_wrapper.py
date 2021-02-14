import json
import requests
from utils import parsers, strings, urls
from praw.models import Submission
from typing import Tuple


# Represents a tuple in the form (URL (str), whether the URL was correctly downloaded (bool))
URLTuple = Tuple[str, bool]


class SubmissionWrapper:

    url_tuples = []

    def __init__(self, submission: Submission, directory: str, png: bool):
        self.submission = submission
        
        r = requests.get(self.submission.url, headers={'Content-type': 'content_type_value'})
        
        if r.status_code == 200:
            self.url_tuples = [(url, self.download(url, self.submission.title, directory, png))
                               for url in parsers.find_urls(r)]


    def download(self, url: str, title: str, directory: str, png: bool) -> bool:
        """
        Downloads image and saves it with the specified title
        :param url: url of the single-image page to scrape the image from
        :param title: title for the image
        :return: True on success, False on failure
        """
        return urls.download_image(url, strings.retitle(title), directory, png=png)

    def count_parsed(self) -> int:
        """
        Counts the number of urls that were parsed
        :return: number of tuples that were correctly parsed
        """
        return sum(1 for x in filter(lambda _, parsed: parsed, self.url_tuples))


    def is_parsed(self) -> bool:
        """
        :return: True if every url associated with the submission was parsed correctly, else False
        """
        return self.count_parsed() == len(self.url_tuples)


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
        """
        Unsaves the submission associated with this post
        """
        self.submission.unsave()