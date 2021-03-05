from collections.abc import Callable
import os
import shutil
import requests
from requests.models import Response


def download(url: str, title: str, directory: str) -> bool:
    """
    Downloads the linked image, converts it to the specified filetype,
    and saves to the specified directory. Avoids name conflicts.
    :param url: url directly linking to the image to download
    :param title: title that the final file should have (WITHOUT an extension)
    :param directory: directory that the final file should be saved to
    :return: True if the file was downloaded correctly, else False
    """
    r = requests.get(url)

    if r.status_code != 200:
        return False

    os.makedirs(directory, exist_ok=True)
    with open(os.path.join(directory, title + get_extension(r)), "wb") as f:
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