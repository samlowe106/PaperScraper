import asyncio
from collections.abc import Callable, Coroutine, Iterable
from typing import Any

from ..core import AsyncClientBundle
from .flickr import flickr_parser
from .imgur import imgur_parser
from .reddit import reddit_parser
from .single_image import single_image_parser

type Parser = Callable[[str, AsyncClientBundle], Coroutine[Any, Any, list[str]]]

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
) -> list[str]:
    """
    Attempts to find images on a linked page by running every parser on it
    :param url: a link to a webpage
    :param parsers: the parsing functions to use
    :return: direct links to the images found, without duplicates, in the order
    the parsers returned them (which keeps gallery order intact)
    """
    parsers = list(parsers)
    results = await asyncio.gather(
        *(parser(url, clients) for parser in parsers), return_exceptions=True
    )
    found: dict[str, None] = {}
    for parser, result in zip(parsers, results, strict=True):
        # one parser failing (an API change, an odd url) shouldn't throw away
        # what the others found, but it shouldn't be silent either
        if isinstance(result, BaseException):
            name = getattr(parser, "__name__", repr(parser))
            print(f"{name} failed on {url}: {result!r}")  # noqa: T201
            continue
        found.update(dict.fromkeys(result))
    return list(found)


__all__ = [
    "Parser",
    "find_urls",
    "flickr_parser",
    "imgur_parser",
    "parsers",
    "reddit_parser",
    "single_image_parser",
]
