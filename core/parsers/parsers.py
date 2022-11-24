import asyncio
from functools import reduce
from typing import Any, Callable, Coroutine, Set

from requests.models import Response

from core import get_extension

from .imgur import imgur_parser


async def single_image(response: Response) -> Set[str]:
    """
    :param response: A web page that has been recognized by this parser
    :returns: A list of all scrapeable urls found in the given webpage
    """
    if get_extension(response).lower() in [".png", ".jpg", ".jpeg", ".gif"]:
        return {response.url}
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
    imgur_parser,
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
