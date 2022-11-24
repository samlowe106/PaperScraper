import os
import re
from typing import Set

import requests
from requests.models import Response

API_ROOT = "https://api.imgur.com/3/"
IMAGE_API = API_ROOT + "image/"
ALBUM_API = API_ROOT + "album/"
GALLERY_API = API_ROOT + "gallery/"

IMGUR_REGEX = re.compile(r"imgur\.com/(a/|gallery/|){0,1}([a-zA-Z]+)\Z")

HEADERS = {"Authorization": f'Client-ID {os.environ["imgur_client_id"]}'}


async def imgur_parser(response: Response) -> Set[str]:
    """
    :param response: a GET response from an imgur (single image, album, or gallery) page
    :return: a set of strings representing all scrape-able images on that page
    """
    m = IMGUR_REGEX.search(response.url)
    if m.group(1) == "":
        # single image
        if m.group(3) is not None:
            # direct link
            return {response.url}
        image_data = requests.get(IMAGE_API + m.group(2), headers=HEADERS)
        if image_data.status_code == 200:
            return {image_data.json()["link"]}
    elif m.group(1) in {"album/", "gallery/"}:
        # album or gallery
        album_response = requests.get(ALBUM_API + m.group(2), headers=HEADERS)
        if album_response.status_code == 200:
            return {
                image_data["link"]
                for image_data in album_response.json()["data"]["images"]
            }
    return set()
