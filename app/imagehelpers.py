from bs4 import BeautifulSoup
from app.filehelpers import save_image
from os.path import splitext
from requests import get

# File extensions that this program should recognize
recognized_extensions = [".png", ".jpg", ".jpeg", ".gif"]


def parse_imgur_album(album_url: str) -> list:
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


def find_urls(url: str) -> list:
    """
    Attempts to find images on a linked page
    Currently supports directly linked images and imgur pages
    :param url: a link to a webpage
    :return: a list of direct links to images found on that webpage
    """

    extension = img_url_extension(url)

    # If the image in the url has a recognized file extension, this is a direct link to an image
    # (Should match artstation, i.imgur.com, i.redd.it, and other direct pages)
    if extension_recognized(extension):
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


def download_image(title: str, url: str, path: str) -> str:
    """
    Attempts to download an image from the given url to a file with the specified title
    :param title: Desired title of the image file
    :param url: A URL containing a direct link to the image to be downloaded
    :param path: The filepath that the file should be saved to
    :return: filepath that the image was downloaded to, empty string if failed
    :raises: IOError, FileNotFoundError
    """

    # Try to download image data
    image = get(url)

    # If the image page couldn't be reached, return an empty string for failure
    if image.status_code != 200:
        # TODO: move error print to main function
        print("\nERROR: Couldn't retrieve image from " + url + " , skipping...")
        return ""

    # Find the file extension
    extension = img_url_extension(url)

    # If the file extension is unrecognized, don't try to download the file
    if not extension_recognized(extension):
        return ""
    else:
        return save_image(image, path, title, extension)


def img_url_extension(url: str) -> str:
    """
    Gets the extension from the given image url
    :param url: the url of an image
    :return: the lowercase extension of that image including the . or "" on failure
    """
    return splitext(url.split('?')[0])[1].lower()


def extension_recognized(extension: str) -> bool:
    """
    Checks if the specified extension is recognized
    :param extension: the extension to check
    :return: True if the extension is recognized, False otherwise
    """
    return extension.lower() in recognized_extensions
