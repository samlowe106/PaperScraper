import os
import re
import shutil
from collections.abc import Callable

import praw
import requests


def sign_in(username: str = None, password: str = None) -> praw.Reddit:
    """
    Signs in to reddit

    :raises OAuthException:
    """
    if username and password:
        return praw.Reddit(
            client_id=os.environ.get("CLIENT_ID"),
            client_secret=os.environ.get("CLIENT_SECRET"),
            user_agent="PaperScraper",
            username=username,
            password=password,
        )
    return praw.Reddit(
        client_id=os.environ.get("CLIENT_ID"),
        client_secret=os.environ.get("CLIENT_SECRET"),
        user_agent="PaperScraper",
    )


def retitle(string: str, title: bool = False) -> str:
    """
    Strips certain punctuation from the start and end of the given string,
    and optionally titlecases it
    :param s: the string to be improved
    :param title: True if the string should be in title case
    :return: a string without certain punctuation at the start or end
    """

    for punctuation in [".", " ", ","]:
        string = trim_string(string, punctuation)

    return title_case(string) if title else string


def trim_string(string1: str, string2: str) -> str:
    """
    Removes any preceding or trailing instances of s2 from s1
    :param s1: the string from which preceding or trailing instances of s2 will be removed
    :param s2: the string that will be removed from the start and end of s1
    :return: s1 without any instances of s2 at either the start or end
    """
    if string2:  # loops won't terminate if string2 is empty
        while string1.startswith(string2):
            string1 = string1.lstrip(string2)

        while string1.endswith(string2):
            string1 = string1.rstrip(string2)

    return string1


def shorten(string: str, max_length: int = 250) -> str:
    """
    Shortens s to be shorter than the specified maximum length, truncating at a
    word if possible. Appends an ellipsis if possible.
    :param s: string to be shortened
    :param max_length: the maximum character length that s can be (defaults to 250)
    :return: s
    :raises IndexError: if max_length is less than 0
    """
    if len(string) <= max_length:
        return string

    # TODO: refactor, shouldn't have mutation in while condition
    while len(string := string.rsplit(" ", 1)[0]) + 3 > max_length and " " in string:
        # Second condition ensures that there's more than one word, and that the loop terminates
        pass

    # truncating at a word failed, just truncate at a character
    if len(string) > max_length:
        string = string[: (max_length - 3)]

    return string + "..."


def title_case(string: str) -> str:
    """
    Capitalizes the first character and all characters immediately after spaces in the given string
    (the string.title() method additionally capitalizes characters after punctuation)
    :param s: the string to be title-cased
    :return: s in title case
    """
    return "".join(
        [
            char.upper() if (i == 0 or string[i - 1] == " ") else char
            for i, char in enumerate(string)
        ]
    )


def remove_invalid(string: str) -> str:
    """
    Removes characters that Windows doesn't allow in filenames from the specified string
    :param s: string to remove characters from
    :return: the given string without invalid characters
    """
    string = string.replace('"', "'")
    for invalid_char in ["\\", "/", ":", "*", "?", "<", ">", "|"]:
        string = string.replace(invalid_char, "")
    return string


def file_title(title: str) -> str:
    """
    Creates a valid, aesthetically pleasing filename based on the given title string
    :param title: the string that the created filename should be based on
    :return: a valid filename
    """
    return shorten(retitle(remove_invalid(title)))


def determine_name(directory: str, title: str, extension: str) -> str:
    """
    Returns a filename based off the given title and extension that is guaranteed to not conflict
    with any of the files in the specified directory
    :param directory: the directory to check the filename against
    :param title: the title to give the file
    :param extension: a string beginning with a .
    representing the extension that the file should have
    """
    # there's a one-line implementation of this function, but it's slower and less legible
    # this regex will match all possible outputs of this function, and is used to guarantee
    #  that the output of this call won't conflict with anything
    pattern = re.compile(
        "^" + re.escape(title) + r"( \(\d+\))?" + re.escape(extension) + "$"
    )
    conflicts = sum(
        1 for filename in os.listdir(directory) if re.match(pattern, filename)
    )
    return os.path.join(
        directory, title + ("" if conflicts == 0 else f" ({conflicts})") + extension
    )


def get_extension(response: requests.models.Response) -> str:
    """
    Gets the extension of the content in the specified response
    :param r: valid request object
    :return: the filetype of the content stored in that request, in lowercase
    """
    return "." + response.headers["Content-type"].split("/")[1].lower()


def sandbox(directory: str) -> Callable:
    """
    Executes function in the specified directory (making that directory if it doesn't already exist)
    then deletes that directory
    """

    def wrapper(function: Callable):
        def make_directory(*args, **kwargs):
            os.makedirs(directory, exist_ok=False)
            original_wd = os.getcwd()
            os.chdir(directory)
            result = function(*args, **kwargs)
            os.chdir(original_wd)
            shutil.rmtree(directory)
            return result

        return make_directory

    return wrapper
