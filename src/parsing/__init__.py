import asyncio
from typing import Any, Callable, Coroutine, Iterable

from ..core import AsyncClientBundle
from .flickr import flickr_parser
from .imgur import imgur_parser
from .reddit import reddit_parser
from .single_image import single_image_parser

type Parser = Callable[[str, AsyncClientBundle], Coroutine[Any, Any, set[str]]]

parsers = (
    single_image_parser,
    reddit_parser,
    imgur_parser,
    flickr_parser,
)


async def find_urls(
    url: str,
    clients: AsyncClientBundle,
    parsers: Iterable[Parser] = parsers,
) -> set[str]:  # we use sets to avoid duplicates
    """
    Attempts to find images on a linked page
    Currently supports directly linked images and imgur pages
    :param url: a link to a webpage
    :param parsing_strategies: a list of parsing functions to use
    :return: a list of direct links to images found on that webpage
    """
    return set().union(
        *(await asyncio.gather(*(parser(url, clients) for parser in parsers)))
    )


__all__ = [
    "find_urls",
    "single_image_parser",
    "imgur_parser",
    "reddit_parser",
    "flickr_parser",
    "get_response_file_extension",
    "Parser",
    "parsers",
]
