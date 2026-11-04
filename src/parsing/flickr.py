import os
import re

from ..core import AsyncClientBundle

# first group is user's name, second is the (numeric) photo id; the id may be
# followed by "/", "/in/album-...", or nothing
_FLICKR_REGEX = re.compile(r"(?:https?://)?(?:www\.)?flickr\.com/photos/([^/]+)/(\d+)")

# first group is the short image id, a base58 encoding of the photo id
SHORT__FLICKR_REGEX = re.compile(r"(?:https?://)?(?:www\.)?flic\.kr/p/([^/?#]+)")

# flickr's base58 alphabet (no 0, O, I, or l)
_BASE58 = "123456789abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ"

API_ROOT = "https://www.flickr.com/services/rest/"


def _decode_base58(short_id: str) -> str | None:
    """Converts a flic.kr short id to a photo id, or None if it isn't base58"""
    number = 0
    for char in short_id:
        if (digit := _BASE58.find(char)) == -1:
            return None
        number = number * 58 + digit
    return str(number)


def _get_flickr_photo_id(url: str) -> str | None:
    """
    :param url: url possibly linking to a flickr image
    :return: the regular id of the image, or None if no id could be found
    """
    if m := SHORT__FLICKR_REGEX.match(url):
        return _decode_base58(m.group(1))

    if m := _FLICKR_REGEX.match(url):
        return m.group(2)

    return None


async def flickr_parser(url: str, clients: AsyncClientBundle) -> list[str]:
    """
    :param url: url possibly linking to a flickr image
    :return: the url of the largest downloadable size of the image, if any
    """
    assert clients.http is not None, "bundle must be entered (async with) first"
    if (photo_id := _get_flickr_photo_id(url)) is None:
        return []

    api_key = os.environ.get("FLICKR_CLIENT_ID")
    if not api_key:  # can't query the API without a key -> skip flickr gracefully
        return []

    response = await clients.http.get(
        API_ROOT,
        params={
            "api_key": api_key,
            "format": "json",
            # plain JSON instead of the default jsonFlickrApi(...) wrapper
            "nojsoncallback": 1,
            "method": "flickr.photos.getSizes",
            "photo_id": photo_id,
        },
    )
    if response.status_code != 200:
        return []

    data = response.json()

    # API errors (bad key, private photo) still come back as 200
    if data.get("stat") != "ok" or data["sizes"]["candownload"] != 1:
        return []

    # flickr sometimes sends dimensions as strings
    biggest_size = max(
        data["sizes"]["size"], key=lambda x: int(x["width"]) * int(x["height"])
    )
    return [biggest_size["source"]]
