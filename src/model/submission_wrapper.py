import json
import os
from typing import List, Tuple
import requests
from requests.models import Response
from praw.models import Submission
from . import parsers, strings, urls

# Represents a tuple in the form (URL (str), whether the URL was correctly downloaded (bool))
URLTuple = Tuple[str, bool]


class SubmissionWrapper:
    """Wraps Submission objects to provide extra functionality"""

    response: Response = None
    urls: List[str] = []
    url_tuples: List[URLTuple] = []
    title = ""
    original_title = ""
    subreddit = ""
    url = ""
    author = ""

    def __init__(self, submission: Submission):
        self.submission = submission
        self.title = submission.title
        self.subreddit = str(submission.subreddit)
        self.url = submission.url
        self.author = str(submission.author)
        self.file_title = strings.file_title(self.submission.title)

        self.response = requests.get(self.submission.url,
                                     headers={'Content-type': 'content_type_value'})

        if self.response.status_code == 200:
            self.urls = parsers.find_urls(self.response)
        else:
            self.urls = []


    def download_all(self, directory: str, title: str = None) -> List[URLTuple]:
        """
        Downloads all urls and bundles them with their results
        :param directory: directory in which to download each file
        :return: a zipped list of each url bundled with a True if the download succeeded
        or False if that download failed
        """
        if title is None:
            title = self.title
        
        results = [urls.download(url, os.path.join(directory, self.title)) if i == 0
                   else urls.download(url, os.path.join(directory, f'{self.title} ({i})'))
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
        """ :return: True if urls were found and each one was parsed, else False """
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


    def __str__(self) -> str:
        """
        Prints out information about the specified post
        :param index: the index number of the post
        :return: None
        """
        return self.format("%t\n   r/%s\n   %u\n   Saved %p / %f image(s) so far.")
        """
        return f"{self.original_title}" \
               f"\n   r/{self.subreddit}" \
               f"\n   {self.url}" \
               f"\n   Saved {self.count_parsed()} / {len(self.url_tuples)} image(s) so far."
        """


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

        for i, char in enumerate(template):
            if specifier_found:

                # Each of these cases represents a different token (%t, %s, etc)
                if char == 't':
                    string_list += self.title
                elif char == 'T':
                    string_list += strings.title_case(self.title)
                elif char == 's':
                    string_list += self.subreddit
                elif char == 'a':
                    string_list += self.author
                elif char == 'u':
                    string_list += self.url
                elif char == 'p':
                    string_list += self.count_parsed()
                elif char == 'f':
                    string_list += len(self.url_tuples)
                elif char == token:
                    string_list += token                
                else:
                    # None of the above cases were satisfied, so this template must be malformed
                    raise ValueError("The given string contains a malformed specifier:\n"
                                    + template
                                    + "\n" + i*" " + "^")
                    
                # we completed this specifier, so we can now look for the next one
                specifier_found = False

            elif char == token:
                # we haven't previously found a format specifier, so this token must be the start of a new one
                specifier_found = True
            else:
                string_list.append(char)
            
        if specifier_found:
            # A format specifier began but was not finished, so this template is malformed
            raise ValueError("The given string contains a trailing token")
            
        return ''.join(string_list)
