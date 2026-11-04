import os
import re

import httpx
from dotenv import load_dotenv

from ..core import AsyncClientBundle

API_ROOT = "https://api.imgur.com/3/"
IMAGE_API = API_ROOT + "image/"
ALBUM_API = API_ROOT + "album/"
GALLERY_API = API_ROOT + "gallery/"

_IMGUR_REGEX = re.compile(
    r"^(http(s)?://)?(www\.)?(?P<direct_link>i\.)?(?P<base_url>imgur\.com)"
    + r"(?P<link_type>/a/|/gallery/|/)(?P<link_id>[^/?#]+)"
    + r"(?P<trailing_slash>/)?"
    + r"(?P<query_string>\?.*)?$"
)

load_dotenv()


def _split_imgur_url(url: str) -> dict[str, str] | None:
    m = _IMGUR_REGEX.match(url)
    return m.groupdict() if m else None


def _get_headers() -> dict[str, str]:
    imgur_client_id = os.environ.get("IMGUR_CLIENT_ID")
    return {"Authorization": f"Client-ID {imgur_client_id}"} if imgur_client_id else {}


async def _handle_single_image(
    url: str, match: dict[str, str], client: httpx.AsyncClient
) -> list[str]:
    if match["direct_link"]:
        # .gifv is an html page wrapping an mp4 of the same name
        return [url.replace(".gifv", ".mp4")]

    # link_id can't contain "/", but may carry an extension (imgur.com/abc.jpg)
    image_id = match["link_id"].split(".")[0]

    response = await client.get(IMAGE_API + image_id, headers=_get_headers())

    if response.status_code != 200:
        return []

    data = response.json().get("data")
    if not isinstance(data, dict):
        return []

    link = data.get("link")
    if isinstance(link, str):
        return [link]

    return []


async def _handle_album(match: dict[str, str], client: httpx.AsyncClient) -> list[str]:
    link_id = match["link_id"].split("-")[-1]
    response = await client.get(f"{ALBUM_API}{link_id}/images", headers=_get_headers())
    if response.status_code != 200:
        return []

    data = response.json().get("data")
    if not isinstance(data, list):
        return []

    return [
        image["link"]
        for image in data
        if isinstance(image, dict) and isinstance(image.get("link"), str)
    ]


async def _handle_gallery(
    match: dict[str, str], client: httpx.AsyncClient
) -> list[str]:
    gallery_id = match["link_id"].split("-")[-1]
    response = await client.get(
        f"{GALLERY_API}album/{gallery_id}", headers=_get_headers()
    )

    if response.status_code != 200:
        return []

    data = response.json().get("data")
    if not isinstance(data, dict):
        return []

    images = data.get("images")
    if not isinstance(images, list):
        return []

    return [
        image["link"]
        for image in images
        if isinstance(image, dict) and isinstance(image.get("link"), str)
    ]


async def imgur_parser(url: str, clients: AsyncClientBundle) -> list[str]:
    """
    Parse an Imgur link using the Imgur API.

    Supports direct image links, albums, and galleries.
    """
    assert clients.http is not None, "bundle must be entered (async with) first"
    match = _split_imgur_url(url)
    if match is None:
        return []

    SINGLE_IMAGE_LINK = "/"
    ALBUM_LINK = "/a/"
    GALLERY_LINK = "/gallery/"

    if match["link_type"] == SINGLE_IMAGE_LINK:
        return await _handle_single_image(url, match, clients.http)

    if match["link_type"] == ALBUM_LINK:
        return await _handle_album(match, clients.http)

    if match["link_type"] == GALLERY_LINK:
        return await _handle_gallery(match, clients.http)

    return []
