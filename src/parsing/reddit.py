from urllib.parse import parse_qs, urljoin, urlparse

import asyncpraw.models
from asyncpraw.exceptions import InvalidURL

from ..core import AsyncClientBundle

# hosts that serve reddit's images directly
_IMAGE_HOSTS = ("i.redd.it", "preview.redd.it")


def _is_reddit_host(host: str) -> bool:
    return host in ("reddit.com", "redd.it") or host.endswith(".reddit.com")


async def reddit_parser(url: str, clients: AsyncClientBundle) -> list[str]:
    """
    :param url: the url to parse
    :param clients: the client bundle; its reddit instance fetches submissions
    :returns: direct links to the images of the reddit post at url, in order
    """
    # crossposts link to their parent with a relative permalink
    url = urljoin("https://www.reddit.com", url)
    parsed = urlparse(url)
    host = parsed.netloc.lower()

    if host in _IMAGE_HOSTS:
        return [url]

    # only reddit urls are submissions; anything else would be misread as a
    # submission id (imgur.com/a/XyZ9 -> post "XyZ9")
    if not _is_reddit_host(host):
        return []

    # reddit.com/media?url=<image> wraps a direct image link
    if parsed.path.rstrip("/") == "/media":
        inner = parse_qs(parsed.query).get("url", [""])[0]
        return [inner] if urlparse(inner).netloc.lower() in _IMAGE_HOSTS else []

    assert clients.reddit is not None, "set_reddit() must be called first"
    try:
        submission = await clients.reddit.submission(url=url)
    except InvalidURL:
        # a subreddit, user page, etc.
        return []

    if urlparse(submission.url).netloc.lower() in _IMAGE_HOSTS:
        return [submission.url]

    # only gallery posts have is_gallery; on others, asyncpraw raises AttributeError
    if getattr(submission, "is_gallery", False):
        return _gallery_urls(submission)

    return []


def _gallery_urls(submission: asyncpraw.models.Submission) -> list[str]:
    """The best available url for each gallery item, in gallery order"""
    urls = []
    for item in submission.gallery_data["items"]:
        metadata = submission.media_metadata.get(item["media_id"], {})
        # deleted or still-processing items have no source
        if metadata.get("status") != "valid":
            continue
        source = metadata.get("s", {})
        # stills have "u"; animated items have "gif" and "mp4" instead
        img_url = source.get("u") or source.get("gif") or source.get("mp4")
        if img_url:
            # reddit html-escapes ampersands in these urls
            urls.append(img_url.replace("&amp;", "&"))
    return urls
