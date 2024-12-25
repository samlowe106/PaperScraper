import os
import re

import requests

INVALID_WINDOWS_CHARS = r'<>:"/\|?*'


def file_title(s: str) -> str:
    """
    Creates a valid filename based on the given title string
    :param s: the string that the created filename should be based on
    :return: a valid filename
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
