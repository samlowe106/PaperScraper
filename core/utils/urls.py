from collections.abc import Callable
import os
import shutil
import re
import requests
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
    pattern = re.compile(f"^{re.escape(title)}( \(\d+\))?{re.escape(extension)}$")
    conflicts = sum(1 for filename in os.listdir(directory) if re.match(pattern, filename))
    return os.path.join(directory, title + ("" if conflicts == 0 else f" ({conflicts})") + extension)


def download(url: str, destination: str) -> bool:
    """
    Downloads the linked image and saves to the specified filepath
    :param url: url directly linking to the image to download
    :param destination: file that the image should be saved to
    :return: True if the file was downloaded correctly, else False
    """
    r = requests.get(url)

    if r.status_code != 200:
        return False

    os.makedirs(os.path.split(destination)[0], exist_ok=True)
    with open(destination, "wb") as f:
        f.write(r.content)
    return True


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
            os.chdir(directory)
            result = function(*args, **kwargs)
            os.chdir("..")
            shutil.rmtree(directory)
            return result
        return make_directory
    return wrapper