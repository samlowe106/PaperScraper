import re

import httpx

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


def get_extension(response: httpx.Response) -> str:
    """
    Gets the extension of the content in the specified response
    :param r: valid request object
    :return: the filetype of the content stored in that request, in lowercase
    """
    return "." + response.headers["Content-type"].split("/")[1].lower()
