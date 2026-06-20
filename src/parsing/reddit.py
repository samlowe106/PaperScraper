from typing import Set
from urllib.parse import urlparse

from ..core import AsyncClientBundle


async def reddit_parser(url: str, clients: AsyncClientBundle) -> Set[str]:
    """
    :param url: the url to parse
    :param client: the http client to use for any requests
    :param reddit: the praw reddit instance to use for parsing
    :returns: A list of all scrapeable urls found in the given webpage
    """

    submission = await clients.reddit.submission(url=url)

    parsed = urlparse(submission.url)

    # single image
    if parsed.netloc in ("i.redd.it", "preview.redd.it"):
        return {submission.url}

    # gallery post
    if submission.is_gallery:
        items = []
        for item in submission.gallery_data["items"]:
            media_id = item["media_id"]

            metadata = submission.media_metadata[media_id]

            # Get the original image and unescape ampersands
            img_url = metadata["s"]["u"].replace("&amp;", "&")
            items.append(img_url)
        return set(items)

    return set()
