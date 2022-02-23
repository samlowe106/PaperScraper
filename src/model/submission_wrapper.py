import json
import os
from typing import Dict
import requests
from praw.models import Submission
from . import parsers, strings, urls


class SubmissionWrapper:
    """Wraps Submission objects to provide extra functionality"""

    def __init__(self, submission: Submission):
        self.submission = submission

        # relevant to user
        self.title = submission.title
        self.subreddit = str(submission.subreddit)
        self.url = submission.url
        self.author = str(submission.author)

        # relevant to parsing
        self.base_file_title = strings.file_title(self.submission.title)
        self.response = requests.get(self.submission.url, headers={'Content-type': 'content_type_value'})
        self.urls_filepaths = {url : "" for url in parsers.find_urls(self.response)} if self.response.status_code == 200 else []


    def download_all(self, directory: str, title: str = None) -> Dict[str, str]:
        """
        Downloads all urls and bundles them with their results
        :param directory: directory in which to download each file
        :return: a zipped list of each url bundled with a True if the download succeeded
        or False if that download failed
        """
        if title is None:
            title = self.title

        for i, url in enumerate(self.urls_filepaths.keys()):
            filename = self.base_file_title if i == 0 else f'{self.base_file_title} ({i})'
            # TODO: this returns a bool!
            self.urls_filepaths[url] = urls.download(url, os.path.join(directory, filename))


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
        return [bool(filepath) for filepath in self.urls_filepaths.values()].count(True)


    def fully_parsed(self) -> bool:
        """ :return: True if urls were found and each one was parsed, else False """
        return self.urls_filepaths and self.count_parsed() == len(self.urls_filepaths)


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
                           "recognized_urls" : self.urls_filepaths
                       }, logfile)


    def __str__(self) -> str:
        """
        Prints out information about the specified post
        :param index: the index number of the post
        :return: None
        """
        return self.format("%t\n   r/%s\n   %u\n   Saved %p / %f image(s) so far.")



    def unsave(self) -> None:
        """ Unsaves this submission """
        self.submission.unsave()


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
            't' : self.title,
            'T' : strings.title_case(self.title),
            's' : self.subreddit,
            'a' : self.author,
            'u' : self.url,
            'p' : self.count_parsed(),
            'f' : len(self.urls_filepaths),
            token : token
            }

        for i, char in enumerate(template):
            if specifier_found:
                if char not in specifier_map:
                    raise ValueError(f"The given string contains a malformed specifier:\n{template}\n{i*' '}^")
                string_list.append(specifier_map[char])
                specifier_found = False
            elif char == token:
                specifier_found = True
            else:
                string_list.append(char)

        if specifier_found:
            # A format specifier began but was not finished, so this template is malformed
            raise ValueError("The given string contains a trailing token")

        return ''.join(string_list)
