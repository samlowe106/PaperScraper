import json
from typing import Set
from bs4 import BeautifulSoup
import requests
from requests.models import Response
from . import urls


class IParser:
    """
    """

    def recognizes(self, r: Response) -> bool:
        """
        :param r: A webpage
        :returns: True if this parser recognizes the given response, else false
        """
        return False

    def try_parse(self, r: Response) -> Set[str]:
        """
        :param r: A web page that has been recognized by this parser
        :returns: A list of all scrapeable urls found in the given webpage
        """
        if not self.recognizes(r):
            return set()

        return self._parse(r)
        
    def _parse(self, r: Response) -> Set[str]:
        """
        Parses the given response.
        """
        raise NotImplementedError("parse() has not yet been implemented for this parser")


class SingleImageParser(IParser):
    """Parses direct links to single images"""

    def __init__(self):
        return


    def recognizes(self, r: Response) -> bool:
        """
        :param r: A webpage
        :returns: True if this parser recognizes the given response, else false
        """
        # If the image in the url has a recognized file extension, this is a direct link to an image
        #  (Should match artstation, i.imgur.com, i.redd.it, and other direct pages)
        return urls.get_extension(r).lower() in [".png", ".jpg", ".jpeg", ".gif"]


    def _parse(self, r: Response) -> Set[str]:
        """
        :param r: A web page that has been recognized by this parser
        :returns: A list of all scrapeable urls found in the given webpage
        """
        return {r.url}


class ImgurParser(IParser):
    """Parses imgur images, albums, and galleries"""

    def __init__(self):
        return


    def recognizes(self, r: Response) -> bool:
        """
        :param r: A webpage
        :returns: True if this parser recognizes the given response, else false
        """
        return "imgur.com" in r.url # and not r.url.endswith("/gallery/")


    def _parse(self, r: Response) -> Set[str]:
        """
        :param r: A web page that has been recognized by this parser
        :returns: A list of all scrapeable urls found in the given webpage
        """
        # Albums
        if "/a/" in r.url:
            return self._parse_album(r.url)

        # Galleries (might be albums or singles)
        elif "/gallery/" in r.url:
            return self._parse_gallery(r.url)

        # Single-image page
        else:
            return {self._parse_single(r.url)}


    def _parse_album(self, album_url: str) -> Set[str]:
        """
        Scrapes the specified imgur album for direct links to each image
        :param album_url: url of an imgur album
        :return: direct links to each image in the specified album
        """
        # Find all the single image pages referenced by this album
        album_page = requests.get(album_url)
        album_soup = BeautifulSoup(album_page.text, "html.parser")
        single_images = ["https://imgur.com/" + div["id"]
                         for div in album_soup.select("div[class=post-images] > div[id]")]
        # Make a list of the direct links to the image hosted on each single-image page;
        #  return the list of all those images
        return {self._parse_single(link) for link in single_images}


    def _parse_gallery(self, url: str) -> Set[str]:
        """
        :param url: url of an imgur gallery
        :returns: a list of all urls of single-image pages that can be found from the given url
        """
        data = requests.get(url + ".json")
        gallery_dict = json.loads(data.content)

        if gallery_dict["data"]["image"]["is_album"]:
            imgur_root, album_id = url.split("gallery")
            return self._parse_album(imgur_root + "a" + album_id)

        raise NotImplementedError("No rule for parsing single-image gallery:\n" + url)
        #return [parse_imgur_single(r.url)]


    def _parse_single(self, url: str) -> str:
        """
        Scrapes regular imgur page for a direct link to the image displayed on that page
        :param url: A single-image imgur page
        :return: A direct link to the image hosted on that page
        """
        page = requests.get(url)
        soup = BeautifulSoup(page.text, "html.parser")
        return soup.select("link[rel=image_src]")[0]["href"]


class FlickrParser(IParser):
    """Parses flickr links"""

    def __init__(self):
        raise NotImplementedError("Class is not yet implemented!")

    """
    def recognizes(self, r: Response) -> bool:
        return False

    def try_parse(self, r: Response) -> 

    def _parse(self, r: Response) -> Set[str]:
        return set()
    """


class GfycatParser(IParser):
    """Parses gfycat links"""

    def __init__(self):
        raise NotImplementedError("Class is not yet implemented!")

    """
    def recognizes(self, r: Response) -> bool:
        return False

    def parse(self, r: Response) -> Set[str]:
        return set()
    """


PARSER_LIST = [SingleImageParser(), ImgurParser()]


def find_urls(r: Response) -> Set[str]:
    """
    Attempts to find images on a linked page
    Currently supports directly linked images and imgur pages
    :param url: a link to a webpage
    :return: a list of direct links to images found on that webpage
    """
    return {url for url in parser.try_parse(r) for parser in PARSER_LIST}
