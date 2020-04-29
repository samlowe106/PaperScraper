from bs4 import BeautifulSoup
from requests import get
from typing import List
import os
from os import listdir, makedirs, remove
from os.path import basename, exists, splitext
from PIL import Image
from typing import Tuple
import ntpath


class ExtensionNotRecognizedError(Exception):
    """
    Raised when a file's extension isn't recognized
    """

# File extensions that this program should recognize
recognized_extensions = [".png", ".jpg", ".jpeg", ".gif"]


def create_directory(dirpath: str) -> None:
    """
    Creates a directory with the specified name if that directory doesn't already exist
    :param dirpath: name of the directory
    :return: None
    """
    if not exists(dirpath):
        makedirs(dirpath)
    return


def convert_file(filepath: str, new_ext: str) -> str:
    """
    Converts the given image to the specified new extension
    :param path: path that the image is located in
    :param filename: title of the file to be converted
    :return: filename (with new extension)
    """
    new_path = ntpath.splitext(filepath)[0] + new_ext
    with Image.open(filepath) as im:
        rgb_im = im.convert('RGB')
        rgb_im.save(new_path)
        # delete old file
        remove(filepath)
    return new_path


def get_file_title(filepath: str) -> str:
    return ntpath.splitext(basename(filepath))[0]


def prevent_conflicts(title: str, extension: str, new_dir: str):
    """
    """
    filename = title + extension
    index = 1
    while filename in listdir(new_dir):
        filename = "{0} ({1}).{2}".format(title, index, extension)
        index += 1

    return filename


def download_image(url: str, dir: str, title: str) -> None:
    """
    Saves the specified image to the specified path with the specified title and file extension
    :param url: a direct link to the image to be saved
    :param dir: the path the image should be saved to
    :param title: the title the image file should have (sans extension)
    :return: None
    """

    image = get(url)

    # The image page couldn't be reached
    if image.status_code != 200:
        return ConnectionError('Request failed with error {0}.'.format(image.status_code))

    # Output path
    create_directory(dir)

    filepath = os.path.join(dir, title + get_extension(url))

    # Write the file
    with open(filepath, "wb") as f:
        f.write(image.content)

    return


def find_urls(url: str) -> List[str]:
    """
    Attempts to find images on a linked page
    Currently supports directly linked images and imgur pages
    :param url: a link to a webpage
    :return: a list of direct links to images found on that webpage
    """

    extension = get_extension(url)

    # If the image in the url has a recognized file extension, this is a direct link to an image
    # (Should match artstation, i.imgur.com, i.redd.it, and other direct pages)
    if is_recognized(extension):
        return [url]

    # Imgur albums
    elif "imgur.com/a/" in url:
        return parse_imgur_album(url)

    # Imgur single-image pages
    elif "imgur.com" in url:
        return [parse_imgur_single(url)]

    # Unrecognized pages
    else:
        return []


def get_extension(url: str) -> str:
    """
    Gets the extension from the given filepath or url
    :param url: a direct link to an image
    :return: the directly-linked image's extension
    """
    # split removes query strings from urls
    return ntpath.splitext(url.split('?')[0])


def is_recognized(extension: str) -> bool:
    """
    Checks if the specified extension is recognized
    :param extension: the extension to check
    :return: True if the extension is recognized, False otherwise
    """
    return extension.lower() in recognized_extensions


def parse_imgur_album(album_url: str) -> List[str]:
    """
    Scrapes the specified imgur album for direct links to each image
    :param album_url: url of an imgur album
    :return: direct links to each image in the specified album
    """
    # Find all the single image pages referenced by this album
    album_page = get(album_url)
    album_soup = BeautifulSoup(album_page.text, "html.parser")
    single_images = ["https://imgur.com/" + div["id"] for div in album_soup.select("div[class=post-images] > div[id]")]
    # Make a list of the direct links to the image hosted on each single-image page; return the list of all those images
    return [parse_imgur_single(link) for link in single_images]


def parse_imgur_single(url: str) -> str:
    """
    Scrapes regular imgur page for a direct link to the image displayed on that page
    :param url: A single-image imgur page
    :return: A direct link to the image hosted on that page
    """
    page = get(url)
    soup = BeautifulSoup(page.text, "html.parser")
    return soup.select("link[rel=image_src]")[0]["href"]
