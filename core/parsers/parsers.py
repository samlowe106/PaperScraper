import asyncio
from functools import reduce
from typing import Any, Callable, Coroutine, Set

import httpx

from core import get_extension

from .flickr import flickr_parser
from .imgur import imgur_parser


async def single_image(url: str) -> Set[str]:
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


PARSERS: Set[Callable[[str], Coroutine[Any, Any, Set[str]]]] = {
    single_image,
    imgur_parser,
    flickr_parser,
}


async def find_urls(url: str) -> Set[str]:
    """
    Attempts to find images on a linked page
    Currently supports directly linked images and imgur pages
    :param url: a link to a webpage
    :return: a list of direct links to images found on that webpage
    """
    return reduce(
        set.union,
        await asyncio.gather(parser(url) for parser in PARSERS),
        set(),
    )
