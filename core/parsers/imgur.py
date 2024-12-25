import os
import re
from typing import Dict, Optional, Set

import httpx
from dotenv import load_dotenv

SINGLE_IMAGE_LINK = ""
ALBUM_LINK = "a/"
GALLERY_LINK = "gallery/"

API_ROOT = "https://api.imgur.com/3/"
IMAGE_API = API_ROOT + "image/"
ALBUM_API = API_ROOT + "album/"
GALLERY_API = API_ROOT + "gallery/"

IMGUR_REGEX = re.compile(
    r"(?P<direct_link>i\.)?"
    + r"(?P<base_url>imgur\.com)"
    + r"(?P<link_type>/a/|/gallery/|/)"
    + r"(?P<link_id>\S+)\Z"
)

load_dotenv()
HEADERS = {"Authorization": f'Client-ID {os.environ["IMGUR_CLIENT_ID"]}'}


def _split_imgur_url(url: str) -> Optional[Dict[str, str]]:
    print(url)
    m = IMGUR_REGEX.search(url)
    return m.groupdict() if m else None


async def imgur_parser(url: str, client: httpx.AsyncClient) -> Set[str]:
    """
    :param response: a GET response from an imgur (single image, album, or gallery) page
    :return: a set of strings representing all scrape-able images on that page
    """
    # might get redirected!
    url = await client.get(url).url

    if (match := _split_imgur_url(url)) is None:
        return set()

    if match["link_type"] == SINGLE_IMAGE_LINK:
        if match["direct_link"]:
            return {url}
        image_data = await client.get(IMAGE_API + match["link_id"], headers=HEADERS)
        if image_data.status_code == 200:
            return {image_data.json()["link"]}
    elif match["link_type"] in {ALBUM_LINK, GALLERY_LINK}:
        album_response = await client.get(ALBUM_API + match["link_id"], headers=HEADERS)
        if album_response.status_code == 200:
            return {
                image_data["link"]
                for image_data in album_response.json()["data"]["images"]
            }
    return set()
