import asyncio
import json
from functools import reduce
from typing import Any, Callable, Coroutine, Iterable, Set

import requests
from bs4 import BeautifulSoup
from requests.models import Response

from core import get_extension


async def single_image(response: Response) -> Set[str]:
    """
    :param response: A web page that has been recognized by this parser
    :returns: A list of all scrapeable urls found in the given webpage
    """
    if get_extension(response).lower() in [".png", ".jpg", ".jpeg", ".gif"]:
        return {response.url}
    return set()


async def imgur_single(response: Response) -> Set[str]:
    """
    Scrapes regular imgur page for a direct link to the image displayed on that page
    :param url: A single-image imgur page
    :return: A direct link to the image hosted on that page
    """
    if (
        "imgur.com" in response.url
        and "/a/" not in response.url
        and "/gallery/" not in response.url
    ):
        page = requests.get(response.url)
        soup = BeautifulSoup(page.text, "html.parser")
        return soup.select("link[rel=image_src]")[0]["href"]
    return set()


async def imgur_gallery(response: Response) -> Set[str]:
    """
    :param url: url of an imgur gallery
    :returns: a list of all urls of single-image pages that can be found from the given url
    """
    data = requests.get(response.url + ".json")
    gallery_dict = json.loads(data.content)

    if gallery_dict["data"]["image"]["is_album"]:
        imgur_root, album_id = response.url.split("gallery")
        gallery_response = requests.get(imgur_root + "a" + album_id)
        if gallery_response.status_code == 200:
            return await imgur_album(gallery_response)

    raise NotImplementedError(
        "No rule for parsing single-image gallery:\n" + response.url
    )
    # return [parse_imgur_single(r.url)]


async def imgur_album(response: Response) -> Set[str]:
    """
    Scrapes the specified imgur album for direct links to each image
    :param album_url: url of an imgur album
    :return: direct links to each image in the specified album
    """
    if "imgur.com" in response.url:  # and not r.url.endswith("/gallery/")
        # Find all the single image pages referenced by this album
        album_soup = BeautifulSoup(response.text, "html.parser")
        single_images = [
            "https://imgur.com/" + div["id"]
            for div in album_soup.select("div[class=post-images] > div[id]")
        ]
        # Make a list of the direct links to the image hosted on each single-image page;
        #  return the list of all those images
        # TODO: is this concurrent?

        return reduce(
            set.union,
            await asyncio.gather(imgur_single(link) for link in single_images),
            set(),
        )
    return set()


async def flickr(response: Response) -> Set[str]:
    """Parses flickr links"""
    return set()
    # raise NotImplementedError("Class is not yet implemented!")


async def gfycat(response: Response) -> Set[str]:
    """Parses gfycat links"""
    return set()
    # raise NotImplementedError("Class is not yet implemented!")


PARSERS: Set[Callable[[Response], Coroutine[Any, Any, Set[str]]]] = {
    single_image,
    imgur_single,
    imgur_album,
    imgur_gallery,
    flickr,
    gfycat,
}


async def find_urls(response: Response) -> Set[str]:
    """
    Attempts to find images on a linked page
    Currently supports directly linked images and imgur pages
    :param url: a link to a webpage
    :return: a list of direct links to images found on that webpage
    """
    return reduce(
        set.union,
        await asyncio.gather(parser(response) for parser in PARSERS),
        set(),
    )
