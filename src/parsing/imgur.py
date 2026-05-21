import os
import re
from typing import Dict, Optional, Set

import httpx
from dotenv import load_dotenv

from ..client_bundle import AsyncClientBundle

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


def _split_imgur_url(url: str) -> Optional[Dict[str, str]]:
    m = _IMGUR_REGEX.match(url)
    return m.groupdict() if m else None


def _get_headers() -> dict[str, str]:
    imgur_client_id = os.environ.get("IMGUR_CLIENT_ID")
    print(f"Using Imgur client ID: {imgur_client_id}")
    return {"Authorization": f"Client-ID {imgur_client_id}"} if imgur_client_id else {}


async def _handle_single_image(
    url: str, match: Dict[str, str], client: httpx.AsyncClient
) -> Set[str]:
    if match["direct_link"]:
        return {url}

    image_id = (
        match["link_id"].split("/")[-1]
        if not match["trailing_slash"]
        else match["link_id"].split("/")[-2]
    )

    response = await client.get(
        f"https://api.imgur.com/3/image/{image_id}", headers=_get_headers()
    )

    if response.status_code != 200:
        return set()

    data = response.json().get("data")
    if not isinstance(data, dict):
        return set()

    link = data.get("link")
    if isinstance(link, str):
        return {link}

    return set()


async def _handle_album(match: Dict[str, str], client: httpx.AsyncClient) -> Set[str]:
    link_id = match["link_id"].split("-")[-1]
    response = await client.get(
        f"https://api.imgur.com/3/album/{link_id}/images", headers=_get_headers()
    )
    if response.status_code != 200:
        return set()

    data = response.json().get("data")
    if not isinstance(data, list):
        return set()

    return {
        image["link"]
        for image in data
        if isinstance(image, dict) and isinstance(image.get("link"), str)
    }


async def _handle_gallery(match: Dict[str, str], client: httpx.AsyncClient) -> Set[str]:
    gallery_id = match["link_id"].split("-")[-1]
    response = await client.get(
        f"https://api.imgur.com/3/gallery/album/{gallery_id}", headers=_get_headers()
    )

    if response.status_code != 200:
        return set()

    data = response.json().get("data")
    if not isinstance(data, dict):
        return set()

    images = data.get("images")
    if not isinstance(images, list):
        return set()

    return {
        image["link"]
        for image in images
        if isinstance(image, dict) and isinstance(image.get("link"), str)
    }


async def imgur_parser(url: str, clients: AsyncClientBundle) -> Set[str]:
    """
    Parse an Imgur link using the Imgur API.

    Supports direct image links, albums, and galleries.
    """
    match = _split_imgur_url(url)
    if match is None:
        return set()

    SINGLE_IMAGE_LINK = "/"
    ALBUM_LINK = "/a/"
    GALLERY_LINK = "/gallery/"

    if match["link_type"] == SINGLE_IMAGE_LINK:
        return await _handle_single_image(url, match, clients.http)

    if match["link_type"] == ALBUM_LINK:
        return await _handle_album(match, clients.http)

    if match["link_type"] == GALLERY_LINK:
        return await _handle_gallery(match, clients.http)

    return set()
