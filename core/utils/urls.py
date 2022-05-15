from collections.abc import Callable
import os
import shutil
import re
from requests.models import Response


def determine_name(directory: str, title: str, extension: str) -> str:
    """
    Returns a filename based off the given title and extension that is guaranteed to not conflict
    with any of the files in the specified directory
    :param directory: the directory to check the filename against
    :param title: the title to give the file
    :param extension: a string beginning with a . representing the extension that the file should have
    """
    # there's a one-line implementation of this function, but it's slower and less legible
    # this regex will match all possible outputs of this function, and is used to guarantee
    #  that the output of this call won't conflict with anything
    pattern = re.compile("^" + re.escape(title) + r"( \(\d+\))?" + re.escape(extension) + "$")
    conflicts = sum(1 for filename in os.listdir(directory) if re.match(pattern, filename))
    return os.path.join(directory, title + ("" if conflicts == 0 else f" ({conflicts})") + extension)


def get_extension(r: Response) -> str:
    """
    Gets the extension of the content in the specified response
    :param r: valid request object
    :return: the filetype of the content stored in that request, in lowercase
    """
    return "." + r.headers["Content-type"].split("/")[1].lower()


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