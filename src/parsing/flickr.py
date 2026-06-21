import json
import os
import re
from typing import Optional, Set

import httpx

from ..core import AsyncClientBundle

# first group is user's name, second is image id
_FLICKR_REGEX = re.compile(
    r"(?:https?://)?(?:www\.)?flickr\.com/photos/([^/]+)/([^/]+)/"
)

# first group is the short image id, which needs to be converted
#  before it can be used in the API
SHORT__FLICKR_REGEX = re.compile(r"(?:https?://)?(?:www\.)?flic\.kr/p/([^/]+)")

API_ROOT = "https://www.flickr.com/services/rest/"


async def _get_flickr_photo_id(url: str, client: httpx.AsyncClient) -> Optional[str]:
    """
    :param url: url possibly linking to a flickr image
    :return: the regular id of the image, or None if no id could be found
    """
    if SHORT__FLICKR_REGEX.match(url):
        response = await client.get(url)
        if response.status_code != 200:
            return None
        url = response.url

    if m := _FLICKR_REGEX.match(url):
        return m.group(2)

    return None


async def flickr_parser(url: str, clients: AsyncClientBundle) -> Set[str]:
    """
    :param url: url possibly linking to a flickr image
    :return: a set of urls of downloadable images
    """
    if (photo_id := await _get_flickr_photo_id(url, clients.http)) is None:
        return set()

    api_key = os.environ.get("FLICKR_CLIENT_ID")
    if not api_key:  # can't query the API without a key -> skip flickr gracefully
        return set()

    parameters = {
        "api_key": api_key,
        "format": "json",
        "method": "flickr.photos.getInfo",
        "photo_id": photo_id,
    }
    response = await clients.http.get(
        API_ROOT + "?" + "&".join(f"{arg}={param}" for arg, param in parameters.items())
    )
    if response.status_code != 200:
        return set()

    data = json.loads(response.text.removeprefix("jsonFlickrApi(").removesuffix(")"))

    if not data["sizes"]["candownload"] == 1:
        return set()

    biggest_size = max(data["sizes"]["size"], key=lambda x: x["width"] * x["height"])
    return {biggest_size["source"]}
