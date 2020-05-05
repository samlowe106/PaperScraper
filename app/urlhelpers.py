import app
from bs4 import BeautifulSoup
import json
import main
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

    # Save the image to a temp directory
    r = requests.get(url)
    
    if r.status_code != 200:
        return False

    extension = get_extension(r)

    temp_filepath = os.path.join(temp_dir, title + extension)

    write_file(r, temp_filepath)

    # Convert to png if necessary
    if png:
        extension = ".png"
        app.filehelpers.convert(temp_filepath, extension)
        # Reassign temp_filepath with new extension
        temp_filepath = os.path.join(temp_dir, title + extension)

    # Move to desired directory
    final_filename = app.filehelpers.prevent_collisions(title, extension, directory)
    final_filepath = os.path.join(directory, final_filename)
    shutil.move(temp_filepath, final_filepath)
    
    # Remove temp file
    os.remove(temp_filepath)

    return True


def get_extension(r: Response) -> str:

    return r.headers["Content-type"].split("/")[1].lower()


def write_file(r: Response, filepath: str) -> bool:
    """
    """
    # Write the file
    with open(filepath, "wb") as f:
        f.write(r.content)

    return True


def find_urls(r: Response) -> List[str]:
    """
    Attempts to find images on a linked page
    Currently supports directly linked images and imgur pages
    :param url: a link to a webpage
    :return: a list of direct links to images found on that webpage
    """

    extension = get_extension(r)

    # If the image in the url has a recognized file extension, this is a direct link to an image
    # (Should match artstation, i.imgur.com, i.redd.it, and other direct pages)
    if recognized(extension):
        return [r.url]

    # Imgur
    elif "imgur.com" in r.url and not r.url.endswith("/gallery/"):
        # Albums    
        if "/a/" in r.url:
            return parse_imgur_album(r.url)

        # Galleries (might be albums or singles)
        elif "/gallery/" in r.url:
            data = requests.get(r.url + ".json")
            gallery_dict = json.loads(data.content)
            if gallery_dict["data"]["image"]["is_album"]:
                return parse_imgur_album(r.url)
            else:
                return [parse_imgur_single(r.url)]

        # Single-image page
        else:
            return [parse_imgur_single(r.url)]

    # Unrecognized pages
    else:
        return []


def recognized(extension: str) -> bool:
    """
    Checks if the specified extension is recognized
    :param extension: the extension to check
    :return: True if the extension is recognized, False otherwise
    """
    return extension in [".png", ".jpg", ".jpeg", ".gif"]


def parse_imgur_album(album_url: str) -> List[str]:
    """
    Scrapes the specified imgur album for direct links to each image
    :param album_url: url of an imgur album
    :return: direct links to each image in the specified album
    """
    # Find all the single image pages referenced by this album
    album_page = requests.get(album_url)
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
    page = requests.get(url)
    soup = BeautifulSoup(page.text, "html.parser")
    return soup.select("link[rel=image_src]")[0]["href"]
