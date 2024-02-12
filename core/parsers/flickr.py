import json
import os
import re
from typing import Optional, Set

import httpx

# first group is user's name, second is image id
FLICKR_REGEX = re.compile(r"flickr\.com/photos/(^/+)/(^/+)/")

# first group is the short image id, which needs to be converted
#  before it can be used in the API
SHORT_FLICKR_REGEX = re.compile(r"flic.kr/p/(^/+)")

API_ROOT = "https://www.flickr.com/services/rest/"


async def _get_flickr_photo_id(url: str, client: httpx.AsyncClient) -> Optional[str]:
    """
    :param url: url possibly linking to a flickr image
    :return: the regular id of the image, or None if no id could be found
    """
    if SHORT_FLICKR_REGEX.match(url):
        response = await client.get(url)
        if response.status_code != 200:
            return None
        url = response.url

    if m := FLICKR_REGEX.match(url):
        return m.group(2)

    return None


async def flickr_parser(url: str, client: httpx.AsyncClient) -> Set[str]:
    """
    :param url: url possibly linking to a flickr image
    :return: a set of urls of downloadable images
    """
    if (photo_id := _get_flickr_photo_id(url, client)) is None:
        return set()

    parameters = {
        "api_key": os.environ["flickr_client_id"],
        "format": "json",
        "method": "flickr.photos.getInfo",
        "photo_id": photo_id,
    }
    response = await client.get(
        API_ROOT + "?" + "&".join(f"{arg}={param}" for arg, param in parameters.items())
    )
    if response.status_code != 200:
        return set()

    data = json.loads(response.text.removeprefix("jsonFlickrApi(").removesuffix(")"))

    if not data["sizes"]["candownload"] == 1:
        return set()

    biggest_size_name = max(
        data["sizes"]["size"], key=lambda x: x["width"] * x["height"]
    )
    return {data["sizes"]["size"][biggest_size_name]["source"]}
