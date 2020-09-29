import app.helpers.parsers
from bs4 import BeautifulSoup
import json
import os
import requests
import shutil
from typing import List
from requests.models import Response


def download_image(url: str, title: str, directory: str, png: bool = False, temp_dir: str = "temp") -> bool:
    """
    Downloads the linked image, converts it to the specified filetype,
    and saves to the specified directory. Avoids name conflicts.
    :param url: url directly linking to the image to download
    :param title: title that the final file should have
    :param dir: directory that the final file should be saved to
    :return: True if the file was downloaded correctly, else False 
    """

    r = requests.get(url)
    if r.status_code != 200:
        return False
    extension = get_extension(r)
    
    # Save the image to a temp directory
    temp_filepath = os.path.join(temp_dir, title + extension)
    write_file(r, temp_filepath)

    # Convert to png if necessary
    if png:
        extension = ".png"
        temp_filepath = app.filehelpers.convert(temp_filepath, extension)

    # Move to desired directory
    shutil.move(temp_filepath, app.filehelpers.prevent_collisions(title, extension, directory))

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
    app.filehelpers.create_directory(os.path.dirname(filepath))
    # Write the file
    with open(filepath, "wb") as f:
        f.write(r.content)

    return
