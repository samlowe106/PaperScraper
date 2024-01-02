from functools import reduce
from typing import Callable, Set

import httpx

from core import get_extension

from .flickr import flickr_parser
from .imgur import imgur_parser


def single_image(url: str) -> Set[str]:
    """
    :param response: A web page that has been recognized by this parser
    :returns: A list of all scrapeable urls found in the given webpage
    """
    response = httpx.get(url)
    if response.status_code == 200 and get_extension(response).lower() in [
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
    ]:
        return {response.url}
    return set()


PARSERS: Set[Callable[[str], Set[str]]] = {
    single_image,
    imgur_parser,
    flickr_parser,
}


def find_urls(url: str) -> Set[str]:
    """
    Attempts to find images on a linked page
    Currently supports directly linked images and imgur pages
    :param url: a link to a webpage
    :return: a list of direct links to images found on that webpage
    """
    return reduce(
        set.union,
        [parser(url) for parser in PARSERS],
        set(),
    )
