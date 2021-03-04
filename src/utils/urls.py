import os
import requests
from requests.models import Response
import utils.files


def download_image(url: str, title: str, directory: str) -> bool:
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

    write_file(r, os.path.join(directory, title + get_extension(r)))
    return True


def get_extension(r: Response) -> str:
    """
    Gets the extension of the content in the specified response
    :param r: valid request object
    :return: the filetype of the content stored in that request, in lowercase
    """
    return "." + r.headers["Content-type"].split("/")[1].lower()


def write_file(r: Response, filepath: str) -> None:
    """
    Writes the content in the specified response to the specified filepath
    :param r: valid response object
    :param filepath: filepath to write the response content to
    :return: None
    """
    utils.files.create_directory(os.path.dirname(filepath))
    # Write the file
    with open(filepath, "wb") as f:
        f.write(r.content)
