import asyncio
from asyncio import Future
from functools import reduce
from typing import Any, Callable, Coroutine, Generator, Iterable

import httpx

from .flickr import flickr_parser
from .imgur import imgur_parser
from .single_image import get_response_file_extension, single_image_parser

parsing_strategies = (
    single_image_parser,
    imgur_parser,
    flickr_parser,
)


async def find_urls(
    url: str,
    client: httpx.AsyncClient,
    parsing_strategies: Iterable[
        Callable[[str, httpx.AsyncClient], Coroutine[Any, Any, set[str]]]
    ] = parsing_strategies,
) -> set[str]:
    """
    Attempts to find images on a linked page
    Currently supports directly linked images and imgur pages
    :param url: a link to a webpage
    :param parsing_strategies: a list of parsing functions to use
    :return: a list of direct links to images found on that webpage
    """
    return set().union(
        *(await asyncio.gather(*(parser(url, client) for parser in parsing_strategies)))
    )


__all__ = [
    "find_urls",
    "single_image_parser",
    "imgur_parser",
    "flickr_parser",
    "get_response_file_extension",
]
