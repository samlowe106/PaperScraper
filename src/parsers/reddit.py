from typing import Set
from urllib.parse import urlparse

from ..client_bundle import AsyncClientBundle

# _REDDIT_REGEX = re.compile(
#    r"^https?://(www\.)?reddit\.com/r/(?P<subreddit>[^/]+)/comments/(?P<submission_id>[^/]+)/[^/]+/)?$"
# )

# "https://redd.it/{submission_id}"


# def _split_reddit_url(url: str) -> Optional[Dict[str, str]]:
#    m = _REDDIT_REGEX.match(url)
#    return m.groupdict() if m else None


async def reddit_parser(url: str, clients: AsyncClientBundle) -> Set[str]:
    """
    :param url: the url to parse
    :param client: the http client to use for any requests
    :param reddit: the praw reddit instance to use for parsing
    :returns: A list of all scrapeable urls found in the given webpage
    """

    submission = clients.reddit.submission(url=url)

    parsed = urlparse(submission.url)

    # single image
    if parsed.netloc == "i.redd.it":
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
